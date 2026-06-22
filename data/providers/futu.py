import pandas as pd
import numpy as np
import futu as ft
from typing import Dict, List, Any, Optional, Tuple
from data.providers.base import BaseProvider

class FutuOpenDProvider(BaseProvider): 
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port

    def fetch_financial_data(self, ticker: str, years: List[int]) -> Dict[str, Any]:
        futu_symbol = self._clean_ticker(ticker)

        # Connect to FutuOpenD
        try:
            quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
        except Exception as exc:
            raise ConnectionError(
                f"Failed to connect to FutuOpenD at {self.host}:{self.port}. "
                f"Error: {exc}. Please make sure FutuOpenD/Moomoo OpenD is running, "
                f"or switch to Yahoo Finance in the sidebar."
            )

        try:
            quote_ctx.start()

            # 1. Fetch Company Name & Metadata
            ret, basic_info = quote_ctx.get_stock_basicinfo(ft.Market.HK, code_list=[futu_symbol])
            company_name = ticker
            if ret == ft.RET_OK and not basic_info.empty:
                company_name = basic_info.iloc[0].get("name", ticker)

            # 2. Fetch Statements (Income, Balance, CashFlow)
            # Fetch and combine financial statement reports
            raw_reports = []
            # In py-futu-api, statement_type integers are: Income=1, BalanceSheet=2, CashFlow=3
            # financial_type for Annual report is 7 (corresponds to F10Type_Annual)
            for stmt_type in [1, 2, 3]:
                ret, data = quote_ctx.get_financials_statements(
                    futu_symbol, 
                    statement_type=stmt_type, 
                    financial_type=7, 
                    num=20
                )
                if ret == ft.RET_OK and "report_list" in data:
                    raw_reports.extend(data["report_list"])
            if ret == ft.RET_OK and "report_list" in data:
                raw_reports.extend(data["report_list"])

            if not raw_reports:
                raise ValueError(f"No annual financial statement reports returned from Futu API for {futu_symbol}.")

            # 3. Clean and map statements to our schema
            reporting_currency = raw_reports[0].get("currency_code", "HKD")
            financials = self._map_futu_reports(raw_reports, years)

            # 4. Fetch Stock Prices to calculate annual average
            # Get historical daily K-lines for stock price averaging
            ret, kline_df, page_req_key = quote_ctx.request_history_kline(
                futu_symbol, 
                start=f"{min(years)}-01-01", 
                end=f"{max(years)}-12-31", 
                ktype=ft.KLType.K_DAY
            )
            
            avg_prices = []
            if ret == ft.RET_OK and not kline_df.empty:
                kline_df["Year"] = pd.to_datetime(kline_df["time_key"]).dt.year
                annual_means = kline_df.groupby("Year")["close"].mean()
                for year in years:
                    avg_prices.append(float(annual_means.get(year, 0.0)))
            else:
                avg_prices = [0.0] * len(years)

            # Fallback for stock price if Close is empty
            ret, snapshot = quote_ctx.get_market_snapshot([futu_symbol])
            current_price = 10.0
            if ret == ft.RET_OK and not snapshot.empty:
                current_price = snapshot.iloc[0].get("last_price", 10.0)
            avg_prices = [p if p > 0 else current_price for p in avg_prices]
            financials["avg_stock_price"] = avg_prices

            # 5. Get Exchange Rates (average and closing)
            exchange_rates, closing_exchange_rates = self._fetch_exchange_rates(quote_ctx, "HKD", reporting_currency, years)

            # 6. Fetch exact buyback shares and money using corporate actions API (HK stocks only)
            buyback_shares_by_year = {year: 0.0 for year in years}
            buyback_money_by_year = {year: 0.0 for year in years}
            min_year = min(years)
            next_key = None
            has_more = True

            while has_more:
                ret, data = quote_ctx.get_corporate_actions_buybacks(futu_symbol, next_key=next_key)
                if ret != ft.RET_OK:
                    raise ValueError(
                        f"Failed to fetch corporate buyback actions for {futu_symbol}. "
                        f"Error: {data}. Please make sure you have the required market data permissions."
                    )

                records = data.get('hk_buy_back_list', [])
                if isinstance(records, pd.DataFrame):
                    if records.empty:
                        break
                    records_list = records.to_dict('records')
                else:
                    if not records:
                        break
                    records_list = records

                reached_end_of_interest = False
                for rec in records_list:
                    # Get date e.g. "2026-04-09"
                    date_str = rec.get("publ_date_str") or rec.get("end_date_str") or ""
                    if not date_str:
                        continue
                    try:
                        rec_year = int(date_str.split("-")[0])
                    except (ValueError, IndexError):
                        continue

                    if rec_year in buyback_shares_by_year:
                        # Sum up exact buyback shares and money
                        buyback_shares_by_year[rec_year] += float(rec.get("buy_back_sum", 0.0))
                        buyback_money_by_year[rec_year] += float(rec.get("buy_back_money", 0.0))

                    # Descending order, break if record year is strictly less than min_year
                    if rec_year < min_year:
                        reached_end_of_interest = True

                if reached_end_of_interest:
                    break

                next_key = data.get("next_key")
                if not next_key:
                    has_more = False

            # Align with requested years list
            financials["buybacks_shares"] = [buyback_shares_by_year[y] for y in years]
            # Convert HKD amount to reporting currency using the fetched exchange rate for each year
            financials["buybacks_paid"] = [
                buyback_money_by_year[y] * rate for y, rate in zip(years, exchange_rates)
            ]

        finally:
            quote_ctx.stop()
            quote_ctx.close()

        return {
            "ticker": ticker,
            "company_name": company_name,
            "currency": reporting_currency,
            "amount_unit": "absolute",
            "market_currency": "HKD", # Futu is configured here for HK market
            "exchange_rate_to_reporting_currency": exchange_rates,
            "closing_exchange_rate_to_reporting_currency": closing_exchange_rates,
            "years": years,
            "financials": financials
        }

    def _clean_ticker(self, ticker: str) -> str:
        """Standardizes ticker to Futu format 'HK.00700'"""
        ticker = ticker.upper().strip()
        if "." in ticker:
            parts = ticker.split(".")
            # If standard Yahoo ticker format like '0700.HK' -> 'HK.00700'
            if parts[1] == "HK":
                code = parts[0]
                if len(code) == 4:
                    code = "0" + code
                return f"HK.{code}"
            return ticker
        # Raw number code e.g., '700' or '0700' -> 'HK.00700'
        if ticker.isdigit():
            code = ticker
            while len(code) < 5:
                code = "0" + code
            return f"HK.{code}"
        return ticker

    def _map_futu_reports(self, raw_reports: List[Dict[str, Any]], years: List[int]) -> Dict[str, List[float]]:
        # Map Futu Field IDs (or typical display name substring match) to our schema
        # We search itemList of each report
        # We define matches using standard Chinese display names found in Futu reports!
        item_definitions = {
            "net_profit": ["归属普通股股东净利润", "归属母公司净利润"],
            "eps": ["基本每股收益", "基本每股盈余", "每股收益", "每股盈余"],
            "ebit": ["营业利润"],
            "interest_expense": ["融资成本", "财务成本", "财务费用"],
            "total_equity": ["归属于母公司股东权益合计", "股东权益合计"],
            "short_term_debt": ["短期借款", "银行贷款及透支"],
            "long_term_debt": ["长期借款", "长期银行贷款"],
            "cash_and_equivalents": ["现金及等价物", "货币资金", "银行存款及现金"],
            "operating_cash_flow": ["经营活动产生的现金流量", "经营活动现金流量净额"],
            "capex": ["资本开支", "资本支出", "购买固定资产", "购买物业、厂房及设备"],
            "da": ["折旧及摊销", "折旧与摊销", "折旧", "摊销"],
            "dividends_paid": ["分配股利", "已付股息-融资", "支付股息", "分红支出"],
            "buybacks_paid": ["回购股份所支付的现金", "回购股份支出", "支付回购股份"],
            "ma_paid": ["收购附属公司"],
            "goodwill": ["商誉"],
            "shares_outstanding": [
                "发行在外股数", "实收资本", "总股本", "普通股股数", 
                "发行在外普通股", "期末普通股股数", "期末发行在外普通股", 
                "期末股份数", "已发行普通股"
            ]
        }

        mapped = {}
        for field in item_definitions.keys():
            mapped[field] = [0.0] * len(years)

        tax_rates = [0.18] * len(years)

        # Build year index
        year_idx = {year: idx for idx, year in enumerate(years)}

        for report in raw_reports:
            rep_year = report.get("fiscal_year")
            if rep_year not in year_idx:
                continue
            idx = year_idx[rep_year]
            item_list = report.get("item_list", [])

            pretax_profit = 0.0
            tax_expense = 0.0

            for item in item_list:
                display_name = item.get("display_name", "")
                val = float(item.get("data", 0.0))

                # Check tax parameters
                if display_name == "税前利润":
                    pretax_profit = val
                if display_name == "所得税":
                    tax_expense = val

                # Map matches
                for field in item_definitions.keys():
                    keywords = item_definitions.get(field, [])
                    if display_name in keywords:
                        # Ensure we don't overwrite with less accurate match
                        if mapped[field][idx] == 0.0:
                            mapped[field][idx] = val

            if pretax_profit > 0:
                tax_rates[idx] = abs(tax_expense / pretax_profit)

        # Post-process: Double Insurance calculation of shares_outstanding
        for idx, year in enumerate(years):
            np_val = mapped["net_profit"][idx]
            eps_val = mapped["eps"][idx]

            # Insurance 1: Try to compute using Net Profit / EPS (highly precise average shares outstanding)
            if eps_val > 0 and np_val > 0:
                mapped["shares_outstanding"][idx] = int(round(np_val / eps_val))

        # Insurance 2: Fallback to basic default value if still missing
        for idx in range(len(years)):
            if mapped["shares_outstanding"][idx] <= 0:
                # 100 million shares as a default
                mapped["shares_outstanding"][idx] = int(100.0 * 1e6)
            else:
                # Ensure all are stored as integers
                mapped["shares_outstanding"][idx] = int(round(mapped["shares_outstanding"][idx]))

        mapped["tax_rate"] = tax_rates

        # Remove internal helper field 'eps'
        mapped.pop("eps", None)

        return mapped

    def _fetch_exchange_rates(self, quote_ctx, market_currency: str, reporting_currency: str, years: List[int]) -> Tuple[List[float], List[float]]:
        """Fetches historical exchange rates dynamically from Yahoo Finance to ensure high precision."""
        market_currency = market_currency.upper()
        reporting_currency = reporting_currency.upper()
        if market_currency == reporting_currency:
            return [1.0] * len(years), [1.0] * len(years)

        # Standardize 'RMB' to 'CNY' for Yahoo Finance query
        std_market = "CNY" if market_currency == "RMB" else market_currency
        std_reporting = "CNY" if reporting_currency == "RMB" else reporting_currency

        if std_market == std_reporting:
            return [1.0] * len(years), [1.0] * len(years)

        # Cross currency ticker format in Yahoo is e.g. 'HKDCNY=X'
        cross_symbol = f"{std_market}{std_reporting}=X"
        import yfinance as yf
        try:
            fx_ticker = yf.Ticker(cross_symbol)
            hist = fx_ticker.history(start=f"{min(years)}-01-01", end=f"{max(years)}-12-31")
            avg_rates = []
            closing_rates = []
            if not hist.empty:
                hist["Year"] = hist.index.year
                annual_means = hist.groupby("Year")["Close"].mean()
                annual_closings = hist.groupby("Year")["Close"].last()
                for year in years:
                    avg_rates.append(float(annual_means.get(year, 1.0)))
                    closing_rates.append(float(annual_closings.get(year, 1.0)))
            else:
                avg_rates = closing_rates = [1.0] * len(years)
            return avg_rates, closing_rates
        except Exception:
            # Fallback for popular pairs if network or API fails
            pair = (market_currency, reporting_currency)
            defaults = {
                ("HKD", "RMB"): 0.86,
                ("HKD", "CNY"): 0.86,
                ("USD", "RMB"): 6.80,
                ("USD", "CNY"): 6.80,
                ("USD", "HKD"): 7.80,
            }
            default_rate = defaults.get(pair) or defaults.get((reporting_currency, market_currency), 1.0)
            if default_rate != 1.0 and defaults.get(pair) is None:
                default_rate = 1.0 / default_rate
            return [default_rate] * len(years), [default_rate] * len(years)
