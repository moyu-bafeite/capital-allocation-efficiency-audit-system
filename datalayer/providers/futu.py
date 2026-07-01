import pandas as pd
import numpy as np
import futu as ft
from typing import Dict, List, Any, Optional, Tuple
from datalayer.providers.base import BaseProvider

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
                f"or upload a custom JSON data file via the sidebar."
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

            if not raw_reports:
                raise ValueError(f"No annual financial statement reports returned from Futu API for {futu_symbol}.")

            # 3. Clean and map statements to our schema
            reporting_currency = raw_reports[0].get("currency_code", "HKD")
            financials = self._map_futu_reports(raw_reports, years)

            # 4. Fetch Stock Prices to calculate annual average (unadjusted, requested yearly)
            avg_prices = []
            closing_prices = []
            for year in years:
                ret, kline_df, page_req_key = quote_ctx.request_history_kline(
                    futu_symbol, 
                    start=f"{year}-01-01", 
                    end=f"{year}-12-31", 
                    ktype=ft.KLType.K_DAY,
                    autype=ft.AuType.NONE
                )
                if ret != ft.RET_OK:
                    raise ValueError(
                        f"Failed to fetch historical stock prices for {futu_symbol} in year {year}. "
                        f"Error: {kline_df}."
                    )
                if kline_df.empty:
                    raise ValueError(
                        f"No historical K-line records returned for {futu_symbol} in year {year}. "
                        f"Please verify if the stock was listed during this period."
                    )
                
                avg_prices.append(float(kline_df["close"].mean()))
                # Year-end closing price = the last trading day's close in the
                # requested year (kline is sorted ascending by date). Used for
                # period-end market cap alongside year-end shares.
                closing_prices.append(float(kline_df.iloc[-1]["close"]))

            financials["avg_stock_price"] = avg_prices
            financials["closing_stock_price"] = closing_prices

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
        """Standardizes ticker to Futu format 'HK.00388'"""
        ticker = ticker.upper().strip()
        if "." in ticker:
            parts = ticker.split(".")
            if parts[1] == "HK":
                code = parts[0]
                if len(code) == 4:
                    code = "0" + code
                return f"HK.{code}"
            return ticker
        # Raw number code e.g., '700' or '0388' -> 'HK.00388'
        if ticker.isdigit():
            code = ticker
            while len(code) < 5:
                code = "0" + code
            return f"HK.{code}"
        return ticker

    def _map_futu_reports(self, raw_reports: List[Dict[str, Any]], years: List[int]) -> Dict[str, List[float]]:
        # Map Futu display_name values to our schema. All keys are English;
        # Futu OpenD returns English display names for HK-listed stocks.
        # Note: some display names differ only by a trailing colon — the
        # income-statement version has no colon (e.g. "Revaluation Surplus")
        # while the cash-flow-statement version has a colon (e.g.
        # "Revaluation Surplus:"). This is how we route values to the correct
        # schema field (income_* vs cashflow_*).
        item_definitions = {
            "net_profit": ["Net Income to Parent Company", "Net Income to Common Stockholders"],
            "eps": ["Basic EPS"],
            "ebit": ["Operating Profit"],
            "special_items_of_operating_profit": ["Special Items of Operating Income"],
            "special_items_of_net_profit": ["Special Items of Pretax Income"],
            "interest_expense": ["Financing Cost"],
            "total_equity": ["Stockholders' Equity"],
            "short_term_debt": ["Bank Loans and Overdrafts"],
            "long_term_debt": ["Long-Term Bank Loan"],
            "lease_liability_current": ["Financial Lease Liabilities-Current Liabilities", "Lease Liabilities - Current Liabilities"],
            "lease_liability_non_current": ["Financial Lease Liabilities-Non-Current", "Lease Liabilities - Non-Current Liabilities", "Lease Liabilities - Non-Current"],
            "convertible_bonds": ["Convertible Notes and Bonds", "Convertible Bonds"],
            "notes_payable": ["Notes Payable"],
            "cash_and_equivalents": ["Cash and Equivalents"],
            "short_term_deposits": ["Short-Term Deposit"],
            "time_deposits_current": ["Fixed Deposit - Current Assets"],
            "time_deposits_non_current": ["Fixed Deposit - Non-Current Assets"],
            "short_term_investment": ["Short-Term Investments"],
            "long_term_investment": ["Long-Term Investments"],
            "fair_value_financial_assets_current": ["Financial Assets at Fair Value - Current Assets"],
            "fair_value_financial_assets_non_current": ["Financial Assets at Fair Value - Non-Current Assets"],
            "derivative_financial_assets_current": ["Derivative Financial Instruments - Current Assets"],
            "derivative_financial_assets_non_current": ["Derivative Financial Instruments - Non-Current Assets"],
            "available_for_sale_financial_assets_current": ["Available for Sale of Financial Assets - Current Assets"],
            "available_for_sale_financial_assets_non_current": ["Available for Sale of Financial Assets - Non-Current Assets"],
            "operating_cash_flow": ["Operating Cash Flow"],
            "capex": ["Purchase of Fixed Assets"],
            "da": ["Depreciation and Amortization:", "Depreciation and Amortization"],
            "dividends_paid": ["Dividends Paid - Financing"],
            "buybacks_paid": [],
            "ma_paid": ["Acquisition of Subsidiaries"],
            "goodwill": ["Goodwill"],
            # Cash-flow-statement non-cash adjustments (used for Owner Earnings).
            # Trailing colon distinguishes cash-flow-statement rows from
            # income-statement rows.
            "cashflow_impairment_adjustment": ["Impairment and Provisions:"],
            "cashflow_fair_value_adjustment": ["Revaluation Surplus:"],
            # Income-statement items used to normalize NOPAT. No trailing colon.
            "income_impairment_charges": ["Impairment and Provision", "Impairment and Provisions"],
            "income_fair_value_changes": ["Revaluation Surplus"],
            "operating_interest_expense": ["Operating Interest Expense"],
            "share_of_profit_associates": ["Share of Profits of Associates"],
            "share_of_profit_joint_venture": ["Share of Profit from Joint Venture Company", "Attributable Share of Joint Ventures and Joint Ventures"],
            "shares_outstanding": []
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
                if display_name in ["Pretax Profit"]:
                    pretax_profit = val
                if display_name in ["Tax"]:
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
        
        mapped["tax_rate"] = tax_rates

        # Fallback: estimate shares_outstanding from net_profit / EPS. This is a
        # rough weighted-average estimate (EPS is itself rounded) and breaks for
        # loss years (EPS=0). It is OVERRIDDEN by authoritative HKEX year-end
        # share-capital data in DataManager._enrich_shares_from_hkex when the
        # monthly-return data has been fetched into the DB. When HKEX data is
        # absent, this fallback (or the normalizer's 100M default) is used.
        for idx, year in enumerate(years):
            np_val = mapped["net_profit"][idx]
            eps_val = mapped["eps"][idx]
            if eps_val != 0:
                mapped["shares_outstanding"][idx] = abs(int(round(np_val / eps_val)))
            # Leave 0.0 when EPS==0 (loss years); DataManager override or the
            # schema's >0 validation handles the rest. Do NOT hard-crash here —
            # that would abort the whole fetch on a single loss year.

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
