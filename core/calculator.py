import pandas as pd
import numpy as np
from typing import Dict, Any, List
from models.input_schema import CompanyAuditInput

class FinancialCalculator:
    def __init__(self, data: CompanyAuditInput, maintenance_capex_ratio: float = 0.5):
        """
        Initialize the FinancialCalculator with structural Pydantic data and configuration.
        
        :param data: CompanyAuditInput pydantic object.
        :param maintenance_capex_ratio: The portion of CapEx that goes to maintaining current business operations (0.0 to 1.0).
        """
        self.data = data
        self.maintenance_capex_ratio = maintenance_capex_ratio
        self.df = self._to_dataframe()
        self._calculate_base_metrics()

    def _to_dataframe(self) -> pd.DataFrame:
        """Converts the schema data into a pandas DataFrame."""
        years = self.data.years
        fin_dict = self.data.financials.model_dump()
        df = pd.DataFrame(fin_dict, index=years)
        df.index.name = "Year"
        return df

    def _calculate_base_metrics(self):
        """Calculates core financial metrics and stores them as columns in the DataFrame."""
        # 1. NOPAT (Net Operating Profit After Taxes)
        self.df["NOPAT"] = self.df["ebit"] * (1 - self.df["tax_rate"])

        # 2. Invested Capital (IC)
        # IC = Equity + Debt - Cash
        total_debt = self.df["short_term_debt"] + self.df["long_term_debt"]
        self.df["total_debt"] = total_debt
        self.df["Invested_Capital"] = self.df["total_equity"] + total_debt - self.df["cash_and_equivalents"]

        # 3. ROIC (Return on Invested Capital)
        # Handle zero or negative Invested Capital gracefully (light asset or net cash companies)
        self.df["ROIC"] = np.where(
            self.df["Invested_Capital"] > 0,
            self.df["NOPAT"] / self.df["Invested_Capital"],
            np.nan
        )

        # 4. Owner Earnings
        # Owner Earnings = Net Profit + D&A - Maintenance CapEx
        maintenance_capex = self.df["capex"] * self.maintenance_capex_ratio
        self.df["maintenance_capex"] = maintenance_capex
        self.df["Owner_Earnings"] = self.df["net_profit"] + self.df["da"] - maintenance_capex

        # 5. Market Capitalization
        self.df["Market_Cap"] = self.df["shares_outstanding_m"] * self.df["avg_stock_price"]

        # 6. Retained Earnings
        # Retained Earnings = Net Profit - Dividends - Buybacks
        self.df["Retained_Earnings_Annual"] = (
            self.df["net_profit"] - self.df["dividends_paid"] - self.df["buybacks_paid"]
        )

    def get_waterfall_data(self, start_year: int = None, end_year: int = None) -> Dict[str, float]:
        """Calculates cumulative cash sources and uses over a specified period or the entire period."""
        df_filtered = self.df
        if start_year is not None and end_year is not None:
            df_filtered = self.df.loc[start_year:end_year]
        elif start_year is not None:
            df_filtered = self.df.loc[start_year:start_year]
            
        total_ocf = df_filtered["operating_cash_flow"].sum()
        if total_ocf <= 0:
            total_ocf = 1e-9  # Avoid division by zero

        total_capex = df_filtered["capex"].sum()
        total_dividends = df_filtered["dividends_paid"].sum()
        total_buybacks = df_filtered["buybacks_paid"].sum()
        total_ma = df_filtered["ma_paid"].sum()
        
        # Calculate the net cash retention/debt change/etc.
        allocated = total_capex + total_dividends + total_buybacks + total_ma
        leftover = total_ocf - allocated

        return {
            "Total_Operating_Cash_Flow": total_ocf,
            "CapEx": total_capex,
            "Dividends": total_dividends,
            "Buybacks": total_buybacks,
            "M_and_A": total_ma,
            "Other_Retention": leftover
        }

    def calculate_rolling_roiic(self, window: int = 3) -> pd.Series:
        """
        Calculates Rolling Incremental ROIC (ROIIC) over a specified year window.
        ROIIC = (NOPAT_t - NOPAT_{t-window}) / (IC_t - IC_{t-window})
        """
        nopat_diff = self.df["NOPAT"].diff(window)
        ic_diff = self.df["Invested_Capital"].diff(window)

        # Handle zero or negative change in Invested Capital
        roiic = np.where(
            (ic_diff > 0) & (self.df["Invested_Capital"] > 0) & (self.df["Invested_Capital"].shift(window) > 0),
            nopat_diff / ic_diff,
            np.nan
        )
        return pd.Series(roiic, index=self.df.index, name=f"ROIIC_{window}Y")

    def calculate_rolling_roiic_retained(self, window: int = 3, lag: int = 0) -> pd.Series:
        """
        Calculates Rolling ROIIC based on Cumulative Retained Earnings.
        ROIIC_retained = (NOPAT_t - NOPAT_{t-window}) / (Cumulative Retained Earnings over window, shifted by lag years)
        """
        if lag < 0:
            raise ValueError("lag must be greater than or equal to 0")

        nopat_diff = self.df["NOPAT"].diff(window)
        
        # lag=1 uses the completed window before the current year, e.g. T, T+1, T+2 for T+3.
        cumulative_retained = self.df["Retained_Earnings_Annual"].rolling(window).sum().shift(lag)

        roiic_retained = np.where(
            cumulative_retained > 0,
            nopat_diff / cumulative_retained,
            np.nan
        )
        return pd.Series(roiic_retained, index=self.df.index, name=f"ROIIC_Retained_{window}Y")

    def calculate_one_dollar_rule(self, window: int = 5) -> pd.Series:
        """
        Calculates Buffet's $1 Rule:
        Market Cap Increase / Cumulative Retained Earnings over a specified window.
        """
        market_cap_diff = self.df["Market_Cap"].diff(window)
        cumulative_retained = self.df["Retained_Earnings_Annual"].rolling(window).sum()

        one_dollar_test = np.where(
            cumulative_retained > 0,
            market_cap_diff / cumulative_retained,
            np.nan
        )
        return pd.Series(one_dollar_test, index=self.df.index, name=f"One_Dollar_Rule_{window}Y")

    def get_processed_df(self, roiic_window_1: int = 3, roiic_window_2: int = 5, roiic_retained_lag: int = 1) -> pd.DataFrame:
        """Returns the fully enriched DataFrame with all computed audit metrics."""
        df_copy = self.df.copy()
        df_copy[f"ROIIC_{roiic_window_1}Y"] = self.calculate_rolling_roiic(roiic_window_1)
        df_copy[f"ROIIC_{roiic_window_2}Y"] = self.calculate_rolling_roiic(roiic_window_2)
        df_copy[f"ROIIC_Retained_{roiic_window_1}Y"] = self.calculate_rolling_roiic_retained(roiic_window_1, lag=roiic_retained_lag)
        df_copy[f"ROIIC_Retained_{roiic_window_2}Y"] = self.calculate_rolling_roiic_retained(roiic_window_2, lag=roiic_retained_lag)
        df_copy[f"One_Dollar_Rule_{roiic_window_1}Y"] = self.calculate_one_dollar_rule(roiic_window_1)
        df_copy[f"One_Dollar_Rule_{roiic_window_2}Y"] = self.calculate_one_dollar_rule(roiic_window_2)
        return df_copy
