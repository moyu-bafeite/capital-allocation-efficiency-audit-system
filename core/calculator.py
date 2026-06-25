import pandas as pd
import numpy as np
from typing import Dict
from models.input_schema import CompanyAuditInput

class FinancialCalculator:
    def __init__(self, data: CompanyAuditInput, maintenance_capex_ratio: float = 0.5):
        """
        Initialize the FinancialCalculator with structural Pydantic data and configuration.
        
        :param data: CompanyAuditInput pydantic object.
        :param maintenance_capex_ratio: The portion of CapEx that goes to maintaining current business operations (0.0 to 1.0).
        """
        if maintenance_capex_ratio < 0 or maintenance_capex_ratio > 1:
            raise ValueError("maintenance_capex_ratio must be between 0 and 1")
        self.data = data
        self.maintenance_capex_ratio = maintenance_capex_ratio
        self.df = self._to_dataframe()
        self._calculate_base_metrics()

    def _to_dataframe(self) -> pd.DataFrame:
        """Converts the schema data into a pandas DataFrame."""
        years = self.data.years
        fin_dict = self.data.financials.model_dump()
        df = pd.DataFrame(fin_dict, index=years)
        df["exchange_rate_to_reporting_currency"] = self.data.exchange_rate_to_reporting_currency
        df["closing_exchange_rate_to_reporting_currency"] = self.data.closing_exchange_rate_to_reporting_currency
        df.index.name = "Year"
        return df

    def _calculate_base_metrics(self):
        """Calculates core financial metrics and stores them as columns in the DataFrame."""
        # 1. NOPAT (Net Operating Profit After Taxes)
        self.df["NOPAT"] = (
            self.df["ebit"] - self.df["special_items_of_operating_profit"] -
            self.df["special_items_of_net_profit"]) * (1 - self.df["tax_rate"])

        # 2. Invested Capital (IC)
        # IC = Equity + Debt - (Cash + Deposits + Short-term & Long-term Cash-like/Financial Assets)
        total_debt = self.df["short_term_debt"] + self.df["long_term_debt"]
        self.df["total_debt"] = total_debt
        total_liquid_cash = (
            self.df["cash_and_equivalents"]
            + self.df["short_term_deposits"]
            + self.df["time_deposits_current"]
            + self.df["time_deposits_non_current"]
            + self.df["short_term_investment"]
            + self.df["long_term_investment"]
            + self.df["fair_value_financial_assets_current"]
            + self.df["fair_value_financial_assets_non_current"]
            + self.df["derivative_financial_assets_current"]
            + self.df["derivative_financial_assets_non_current"]
            + self.df["available_for_sale_financial_assets_current"]
        )
        self.df["Invested_Capital"] = self.df["total_equity"] + total_debt - total_liquid_cash

        # 3. ROIC (Return on Invested Capital)
        # Calculate ROIC based on Average Invested Capital over the current and previous year
        # Fallback to the current year's end-of-period Invested Capital for the first year
        average_ic = (self.df["Invested_Capital"] + self.df["Invested_Capital"].shift(1)) / 2
        average_ic = average_ic.fillna(self.df["Invested_Capital"])
        
        self.df["ROIC"] = np.where(
            average_ic > 0,
            self.df["NOPAT"] / average_ic,
            np.nan
        )

        # 4. Owner Earnings
        # Owner Earnings = Net Profit + D&A + Impairments - Fair Value Changes - Maintenance CapEx
        maintenance_capex = self.df["capex"] * self.maintenance_capex_ratio
        self.df["maintenance_capex"] = maintenance_capex
        self.df["Owner_Earnings"] = (
            self.df["net_profit"]
            + self.df["da"]
            + self.df["impairment_charges"]
            - self.df["fair_value_changes"]
            - maintenance_capex
        )

        # 5. Market Capitalization, converted to the reporting currency and matched to amount_unit.
        self.df["avg_stock_price_reporting_currency"] = (
            self.df["avg_stock_price"] * self.df["exchange_rate_to_reporting_currency"]
        )
        raw_market_cap = self.df["shares_outstanding"] * self.df["avg_stock_price_reporting_currency"]
        if self.data.amount_unit == "million":
            self.df["Market_Cap"] = raw_market_cap / 1e6
        else:
            self.df["Market_Cap"] = raw_market_cap

        # 6. Retained Earnings
        # Retained Earnings = Net Profit - Dividends - Buybacks
        self.df["Retained_Earnings_Annual"] = (
            self.df["net_profit"] - self.df["dividends_paid"] - self.df["buybacks_paid"]
        )

        # 7. Goodwill & M&A Capital Efficiency Ratios
        # Gauge whether management is building an empire via premium acquisitions.
        self.df["Goodwill_to_Equity"] = np.where(
            self.df["total_equity"] > 0,
            self.df["goodwill"] / self.df["total_equity"],
            np.nan
        )
        self.df["Goodwill_to_IC"] = np.where(
            self.df["Invested_Capital"] > 0,
            self.df["goodwill"] / self.df["Invested_Capital"],
            np.nan
        )
        self.df["MA_to_OCF"] = np.where(
            self.df["operating_cash_flow"] > 0,
            self.df["ma_paid"] / self.df["operating_cash_flow"],
            np.nan
        )

        # 8. Free Cash Flow & Earnings Quality
        # Buffett's owner-earnings philosophy: cash, not accounting accruals, is truth.
        self.df["FCF"] = self.df["operating_cash_flow"] - self.df["capex"]
        self.df["OE_to_NetProfit"] = np.where(
            self.df["net_profit"] > 0,
            self.df["Owner_Earnings"] / self.df["net_profit"],
            np.nan
        )
        self.df["FCF_to_NetIncome"] = np.where(
            self.df["net_profit"] > 0,
            self.df["FCF"] / self.df["net_profit"],
            np.nan
        )
        self.df["Accruals_Ratio"] = np.where(
            self.df["Invested_Capital"] > 0,
            (self.df["net_profit"] - self.df["operating_cash_flow"]) / self.df["Invested_Capital"],
            np.nan
        )
        # Owner Earnings Per Share (OEPS) - Buffett's true per-share growth yardstick.
        shares_for_eps = (
            self.df["shares_outstanding"] / 1e6
            if self.data.amount_unit == "million"
            else self.df["shares_outstanding"]
        )
        self.df["OEPS"] = np.where(
            shares_for_eps > 0,
            self.df["Owner_Earnings"] / shares_for_eps,
            np.nan
        )

    def get_waterfall_data(self, start_year: int = None, end_year: int = None) -> Dict[str, float]:
        """Calculates cumulative cash sources and uses over a specified period or the entire period."""
        if start_year is not None and end_year is not None and start_year > end_year:
            raise ValueError("start_year must be less than or equal to end_year")
        df_filtered = self.df
        if start_year is not None and end_year is not None:
            df_filtered = self.df.loc[start_year:end_year]
        elif start_year is not None:
            df_filtered = self.df.loc[start_year:start_year]

        total_ocf = df_filtered["operating_cash_flow"].sum()

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
        if window <= 0:
            raise ValueError("window must be greater than 0")
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
        if window <= 0:
            raise ValueError("window must be greater than 0")
        if lag < 0:
            raise ValueError("lag must be greater than or equal to 0")

        nopat_diff = self.df["NOPAT"].diff(window)

        # lag=1 uses the completed window before the current year, e.g. T, T+1, T+2 for T+3.
        cumulative_retained = self.df["Retained_Earnings_Annual"].rolling(window).sum().shift(lag)

        roiic_retained = np.where(
            cumulative_retained > 0,
            nopat_diff / cumulative_retained,
            np.where(
                (cumulative_retained <= 0) & (nopat_diff > 0),
                np.inf,
                np.nan
            )
        )
        return pd.Series(roiic_retained, index=self.df.index, name=f"ROIIC_Retained_{window}Y")

    def calculate_acquisition_roiic(self, window: int = 3, lag: int = 0) -> pd.Series:
        """
        Calculates Acquisition ROIIC: incremental NOPAT generated per unit of cash deployed on M&A.
        Acquisition_ROIIC = (NOPAT_t - NOPAT_{t-window}) / (Cumulative ma_paid over window, shifted by lag years)
        Mirrors ROIIC_Retained but isolates acquisition capital from total retained earnings,
        surfacing "empire builders" whose M&A spend fails to clear the cost of capital.
        """
        if window <= 0:
            raise ValueError("window must be greater than 0")
        if lag < 0:
            raise ValueError("lag must be greater than or equal to 0")

        nopat_diff = self.df["NOPAT"].diff(window)
        cumulative_ma = self.df["ma_paid"].rolling(window).sum().shift(lag)

        acquisition_roiic = np.where(
            cumulative_ma > 0,
            nopat_diff / cumulative_ma,
            np.nan
        )
        return pd.Series(acquisition_roiic, index=self.df.index, name=f"Acquisition_ROIIC_{window}Y")

    def calculate_growth_diff(self, window: int, col_a: str, col_b: str) -> pd.Series:
        """
        Calculates the difference in cumulative growth rates between two columns over a window.
        Returns (col_a growth - col_b growth). Positive when col_a outpaces col_b.
        """
        if window <= 0:
            raise ValueError("window must be greater than 0")

        a_start = self.df[col_a].shift(window)
        b_start = self.df[col_b].shift(window)
        a_growth = np.where(a_start > 0, (self.df[col_a] - a_start) / a_start, np.nan)
        b_growth = np.where(b_start > 0, (self.df[col_b] - b_start) / b_start, np.nan)
        return pd.Series(
            a_growth - b_growth,
            index=self.df.index,
            name=f"{col_a}_vs_{col_b}_Growth_{window}Y",
        )

    def calculate_one_dollar_rule(self, window: int = 5) -> pd.Series:
        """
        Calculates Buffet's $1 Rule:
        Market Cap Increase / Cumulative Retained Earnings over a specified window.
        """
        if window <= 0:
            raise ValueError("window must be greater than 0")
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
        if roiic_window_1 <= 0 or roiic_window_2 <= 0:
            raise ValueError("ROIIC windows must be greater than 0")
        if roiic_retained_lag < 0:
            raise ValueError("roiic_retained_lag must be greater than or equal to 0")
        df_copy = self.df.copy()
        df_copy[f"ROIIC_{roiic_window_1}Y"] = self.calculate_rolling_roiic(roiic_window_1)
        df_copy[f"ROIIC_{roiic_window_2}Y"] = self.calculate_rolling_roiic(roiic_window_2)
        df_copy[f"ROIIC_Retained_{roiic_window_1}Y"] = self.calculate_rolling_roiic_retained(roiic_window_1, lag=roiic_retained_lag)
        df_copy[f"ROIIC_Retained_{roiic_window_2}Y"] = self.calculate_rolling_roiic_retained(roiic_window_2, lag=roiic_retained_lag)
        df_copy[f"One_Dollar_Rule_{roiic_window_1}Y"] = self.calculate_one_dollar_rule(roiic_window_1)
        df_copy[f"One_Dollar_Rule_{roiic_window_2}Y"] = self.calculate_one_dollar_rule(roiic_window_2)
        df_copy[f"Acquisition_ROIIC_{roiic_window_1}Y"] = self.calculate_acquisition_roiic(roiic_window_1, lag=roiic_retained_lag)
        df_copy[f"Acquisition_ROIIC_{roiic_window_2}Y"] = self.calculate_acquisition_roiic(roiic_window_2, lag=roiic_retained_lag)
        df_copy[f"Goodwill_vs_NOPAT_Growth_{roiic_window_2}Y"] = self.calculate_growth_diff(roiic_window_2, "goodwill", "NOPAT")
        return df_copy
