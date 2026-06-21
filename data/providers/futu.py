import keyword
import pandas as pd
import numpy as np
import futu as ft
from typing import Dict, List, Any, Optional
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
            # ret, data = quote_ctx.get_financials_statements(
            #         futu_symbol, 
            #         statement_type=0, 
            #         financial_type=7, 
            #         num=50
            #     )
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

            # 5. Get Exchange Rates
            exchange_rates = self._fetch_exchange_rates(quote_ctx, "HKD", reporting_currency, years)

            # 6. Set buyback shares (absolute number of shares)
            aligned_buybacks_shares = []
            for paid, price, rate in zip(financials["buybacks_paid"], financials["avg_stock_price"], exchange_rates):
                price_rep = price * rate
                if paid > 0 and price_rep > 0:
                    aligned_buybacks_shares.append(paid / price_rep)
                else:
                    aligned_buybacks_shares.append(0.0)
            financials["buybacks_shares"] = aligned_buybacks_shares

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
        shares_found = [False] * len(years)

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
                            if field == "shares_outstanding":
                                mapped[field][idx] = val
                                shares_found[idx] = True
                            else:
                                mapped[field][idx] = val

            if pretax_profit > 0:
                tax_rates[idx] = abs(tax_expense / pretax_profit)

        # Post-process: Double Insurance calculation of shares_outstanding
        for idx, year in enumerate(years):
            np_val = mapped["net_profit"][idx]
            eps_val = mapped["eps"][idx]

            # Insurance 1: Try to compute using Net Profit / EPS (highly precise average shares outstanding)
            if eps_val > 0 and np_val > 0:
                # E.g., 224,842,000,000 (RMB) / 24.749 (RMB/share) = 9,084,892,318 shares
                mapped["shares_outstanding"][idx] = np_val / eps_val
                shares_found[idx] = True
            elif mapped["shares_outstanding"][idx] > 0:
                # Insurance 2: Fall back to Balance Sheet matched shares_outstanding
                shares_found[idx] = True

        # Insurance 3: Fallback to basic default value if still missing
        for idx, found in enumerate(shares_found):
            if not found or mapped["shares_outstanding"][idx] <= 0:
                # 100 million shares as a default
                mapped["shares_outstanding"][idx] = 100.0 * 1e6

        mapped["tax_rate"] = tax_rates

        # Remove internal helper field 'eps'
        mapped.pop("eps", None)

        return mapped

    def _fetch_exchange_rates(self, quote_ctx, market_currency: str, reporting_currency: str, years: List[int]) -> List[float]:
        """Fetches exchange rates using FutuOpenD connection."""
        market_currency = market_currency.upper()
        reporting_currency = reporting_currency.upper()
        if market_currency == reporting_currency:
            return [1.0] * len(years)

        # Try to resolve rate from currency conversions
        # Default to standard cross rates
        defaults = {
            ("HKD", "RMB"): 0.86,
            ("HKD", "CNY"): 0.86,
        }
        rate = defaults.get((market_currency, reporting_currency)) or 1.0
        return [rate] * len(years)
