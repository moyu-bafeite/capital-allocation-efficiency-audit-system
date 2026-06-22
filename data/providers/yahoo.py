import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from data.providers.base import BaseProvider

class YahooFinanceProvider(BaseProvider):
    def fetch_financial_data(self, ticker: str, years: List[int]) -> Dict[str, Any]:
        """
        Fetches historical financial data from Yahoo Finance.
        Adjusts symbol format from HK.00700 (Futu) or 0700.HK (Yahoo) automatically.
        """
        yahoo_symbol = self._clean_ticker(ticker)
        ticker_obj = yf.Ticker(yahoo_symbol)

        # 1. Fetch Company Name and Currency info
        info = ticker_obj.info
        company_name = info.get("longName") or info.get("shortName") or ticker
        market_currency = info.get("currency") or "HKD"
        
        # Hong Kong stocks usually report in HKD or RMB. We check financial currency.
        # Yahoo financials currency is sometimes retrieved from info or default to market_currency
        reporting_currency = info.get("financialCurrency") or market_currency

        # 2. Fetch Statements
        income_stmt = ticker_obj.income_stmt
        balance_sheet = ticker_obj.balance_sheet
        cashflow = ticker_obj.cashflow

        # Extract years and map statement data
        statements = {
            "income": income_stmt,
            "balance": balance_sheet,
            "cashflow": cashflow
        }

        # Format column names to just year integers
        for key, df in statements.items():
            if df is not None and not df.empty:
                df.columns = [pd.Timestamp(col).year for col in df.columns]
                statements[key] = df

        # Align financial items
        financials = self._map_financials(statements, years)

        # 3. Fetch Stock Prices & calculate annual average
        hist = ticker_obj.history(start=f"{min(years)}-01-01", end=f"{max(years)}-12-31")
        avg_prices = []
        if not hist.empty:
            hist["Year"] = hist.index.year
            annual_means = hist.groupby("Year")["Close"].mean()
            for year in years:
                avg_prices.append(float(annual_means.get(year, 0.0)))
        else:
            avg_prices = [0.0] * len(years)
        
        # Fill in average price if close is missing using some fallback (info current price)
        current_price = info.get("currentPrice") or info.get("previousClose") or 10.0
        avg_prices = [p if p > 0 else current_price for p in avg_prices]
        financials["avg_stock_price"] = avg_prices

        # 4. Fetch Exchange Rates (average and closing)
        exchange_rates, closing_exchange_rates = self._fetch_exchange_rates(market_currency, reporting_currency, years)

        # 5. Get shares outstanding (fallback to current if series is empty)
        shares_series = ticker_obj.get_shares_full(start=f"{min(years)}-01-01", end=f"{max(years)}-12-31")
        aligned_shares = []
        current_shares = info.get("sharesOutstanding") or 100.0
        
        if shares_series is not None and not shares_series.empty:
            shares_df = pd.DataFrame(shares_series)
            shares_df["Year"] = shares_df.index.year
            annual_shares = shares_df.groupby("Year")[0].last()
            for year in years:
                aligned_shares.append(float(annual_shares.get(year, current_shares)))
        else:
            # Try to get from shares outstanding if it's a list in financials, or fallback to current
            # In Yahoo balance sheet, Common Stock Shares Outstanding is sometimes available
            bs_df = statements["balance"]
            bs_shares = self._find_row(bs_df, ["Share Issued", "Ordinary Shares Number", "Common Stock Shares Outstanding"])
            if bs_shares is not None:
                for year in years:
                    aligned_shares.append(float(bs_shares.get(year, current_shares)))
            else:
                aligned_shares = [float(current_shares)] * len(years)
        
        financials["shares_outstanding"] = aligned_shares

        # Set buybacks shares based on buybacks paid / avg stock price (reporting currency)
        aligned_buybacks_shares = []
        for paid, price, rate in zip(financials["buybacks_paid"], financials["avg_stock_price"], exchange_rates):
            price_rep = price * rate
            if paid > 0 and price_rep > 0:
                # Since buybacks_paid is in millions (for Yahoo), buybacks_paid * 1e6 gives absolute paid
                aligned_buybacks_shares.append((paid * 1e6) / price_rep)
            else:
                aligned_buybacks_shares.append(0.0)
        
        financials["buybacks_shares"] = aligned_buybacks_shares

        return {
            "ticker": ticker,
            "company_name": company_name,
            "currency": reporting_currency,
            "amount_unit": "million",
            "market_currency": market_currency,
            "exchange_rate_to_reporting_currency": exchange_rates,
            "closing_exchange_rate_to_reporting_currency": closing_exchange_rates,
            "years": years,
            "financials": financials
        }

    def _clean_ticker(self, ticker: str) -> str:
        """Standardizes Futu symbol 'HK.00700' -> '0700.HK'"""
        ticker = ticker.upper().strip()
        if ticker.startswith("HK."):
            code = ticker.split(".")[1]
            # Strip extra leading zeros to match 0700.HK, or leave 4 digits
            if len(code) > 4 and code.startswith("0"):
                code = code[1:]
            return f"{code}.HK"
        return ticker

    def _find_row(self, df: pd.DataFrame, keys: List[str]) -> Any:
        """Finds a row in DataFrame by matching any of the alternative labels."""
        if df is None or df.empty:
            return None
        for key in keys:
            # Exact match first
            if key in df.index:
                return df.loc[key]
            # Case insensitive & partial match fallback
            matches = [idx for idx in df.index if key.lower() in str(idx).lower()]
            if matches:
                return df.loc[matches[0]]
        return None

    def _map_financials(self, statements: Dict[str, pd.DataFrame], years: List[int]) -> Dict[str, List[float]]:
        # Row definitions with alternative matches
        row_definitions = {
            "net_profit": (["Net Income Common Stockholders", "Net Income", "Net Income Attr to Common Shareholders", "Net Income From Continuing Operations Net Of Minority Interest"], "income"),
            "ebit": (["EBIT", "Operating Income", "Operating Profit"], "income"),
            "interest_expense": (["Interest Expense", "Interest Expense Non Operating", "Finance Costs"], "income"),
            "total_equity": (["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity", "Total Assets - Total Liabilities"], "balance"),
            "short_term_debt": (["Current Debt", "Short Term Debt", "Short Long Term Debt", "Short-Term Debt", "Current Portions Of Long Term Debt"], "balance"),
            "long_term_debt": (["Long Term Debt", "Long-Term Debt", "Long Term Debt And Capital Lease Obligation", "Non Current Deferred Liabilities"], "balance"),
            "cash_and_equivalents": (["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash", "Cash Financial"], "balance"),
            "operating_cash_flow": (["Operating Cash Flow", "Cash Flow From Continuing Operating Activities", "Net Cash Provided By Operating Activities"], "cashflow"),
            "capex": (["Capital Expenditure", "Purchase Of Property Plant And Equipment", "Net PPE Purchase And Sale", "PPE Purchase"], "cashflow"),
            "da": (["Depreciation And Amortization", "Depreciation Amortization Depletion", "Depreciation"], "cashflow"),
            "dividends_paid": (["Cash Dividends Paid", "Common Stock Dividend Paid", "Dividends Paid"], "cashflow"),
            "buybacks_paid": (["Repurchase Of Capital Stock", "Common Stock Repurchased", "Share Repurchase", "Treasury Stock Shares"], "cashflow"),
            "ma_paid": (["Business Acquisition Or Divestiture", "Net Business Acquisitions Disposals", "Acquisitions"], "cashflow"),
            "goodwill": (["Goodwill", "Good Will"], "balance")
        }

        mapped = {}
        for field, (labels, stmt_key) in row_definitions.items():
            df = statements[stmt_key]
            row_data = self._find_row(df, labels)
            
            aligned_values = []
            for year in years:
                val = 0.0
                if row_data is not None:
                    # In yfinance pandas DF, sometimes row_data is a Series or a scalar (if only 1 col)
                    if isinstance(row_data, pd.Series):
                        raw_val = row_data.get(year, 0.0)
                    else:
                        raw_val = row_data
                    
                    # Convert pandas NaNs/None to 0.0
                    if pd.isna(raw_val):
                        val = 0.0
                    else:
                        val = float(raw_val)
                aligned_values.append(val)
            
            # Unit standardization to million (yfinance returns absolute numbers like 28,000,000,000)
            # We divide by 1e6 to convert to million. Note that tax_rate is a percentage, so don't divide!
            mapped[field] = [v / 1e6 for v in aligned_values]

        # Special extraction for tax rate
        tax_rates = []
        inc_df = statements["income"]
        pretax = self._find_row(inc_df, ["Pretax Income", "Tax Loss Carry Forward"])
        tax_prov = self._find_row(inc_df, ["Tax Provision", "Income Tax Expense"])
        tax_rate_row = self._find_row(inc_df, ["Tax Rate For Calcs", "Effective Tax Rate"])
        
        for year in years:
            rate = 0.18 # Conservative default
            if tax_rate_row is not None:
                if isinstance(tax_rate_row, pd.Series):
                    rate = float(tax_rate_row.get(year, 0.18))
                else:
                    rate = float(tax_rate_row)
            elif pretax is not None and tax_prov is not None:
                p_val = pretax.get(year, 0.0) if isinstance(pretax, pd.Series) else pretax
                t_val = tax_prov.get(year, 0.0) if isinstance(tax_prov, pd.Series) else tax_prov
                if p_val and p_val > 0 and t_val and t_val > 0:
                    rate = t_val / p_val
            
            # Ensure boundaries
            if pd.isna(rate) or rate < 0 or rate > 1:
                rate = 0.18
            tax_rates.append(rate)
        
        mapped["tax_rate"] = tax_rates

        return mapped

    def _fetch_exchange_rates(self, market_currency: str, reporting_currency: str, years: List[int]) -> Tuple[List[float], List[float]]:
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
