import unittest
import numpy as np

from core.calculator import FinancialCalculator
from models.input_schema import CompanyAuditInput


def make_sample_input() -> CompanyAuditInput:
    return CompanyAuditInput(
        ticker="TEST",
        company_name="Test Company",
        currency="USD",
        amount_unit="million",
        market_currency="USD",
        exchange_rate_to_reporting_currency=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        closing_exchange_rate_to_reporting_currency=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        years=[2020, 2021, 2022, 2023, 2024, 2025],
        financials={
            "net_profit": [100, 120, 140, 160, 180, 200],
            "ebit": [120, 150, 180, 210, 240, 270],
            "tax_rate": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
            "interest_expense": [5, 5, 5, 5, 5, 5],
            "total_equity": [500, 550, 600, 650, 700, 750],
            "short_term_debt": [50, 50, 50, 50, 50, 50],
            "long_term_debt": [100, 100, 100, 100, 100, 100],
            "cash_and_equivalents": [50, 50, 50, 50, 50, 50],
            "operating_cash_flow": [130, 150, 170, 190, 210, 230],
            "capex": [40, 40, 40, 40, 40, 40],
            "da": [20, 20, 20, 20, 20, 20],
            "dividends_paid": [20, 20, 20, 20, 20, 20],
            "buybacks_paid": [0, 0, 10, 0, 20, 0],
            "buybacks_shares": [0, 0, 1000000, 0, 2000000, 0],
            "ma_paid": [5, 5, 5, 5, 5, 5],
            "goodwill": [10, 10, 10, 10, 10, 10],
            "shares_outstanding": [100000000, 99000000, 98000000, 97000000, 96000000, 95000000],
            "avg_stock_price": [10, 11, 12, 13, 14, 15],
        },
    )


class FinancialCalculatorTest(unittest.TestCase):
    def test_base_metrics_are_calculated(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df

        self.assertEqual(df.loc[2020, "NOPAT"], 96)
        self.assertEqual(df.loc[2020, "Invested_Capital"], 600)
        self.assertEqual(df.loc[2020, "Owner_Earnings"], 100)
        self.assertEqual(df.loc[2020, "Market_Cap"], 1000)

    def test_processed_df_contains_roiic_and_one_dollar_rule(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        self.assertIn("ROIIC_Retained_3Y", df.columns)
        self.assertIn("ROIIC_Retained_5Y", df.columns)
        self.assertIn("One_Dollar_Rule_5Y", df.columns)
        self.assertAlmostEqual(df.loc[2023, "ROIIC_Retained_3Y"], 72 / 290)

    def test_invalid_maintenance_capex_ratio_is_rejected(self):
        with self.assertRaises(ValueError):
            FinancialCalculator(make_sample_input(), maintenance_capex_ratio=1.5)

    def test_owner_earnings_with_non_cash_adjustments(self):
        sample_input = make_sample_input()
        # Set non-cash adjustments for 2020 (index 0) and 2021 (index 1)
        sample_input.financials.impairment_charges = [15.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sample_input.financials.fair_value_changes = [-10.0, 30.0, 0.0, 0.0, 0.0, 0.0]

        calculator = FinancialCalculator(sample_input, maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: net_profit(100) + da(20) + impairment_charges(15) - fair_value_changes(-10) - maintenance_capex(20)
        # = 100 + 20 + 15 - (-10) - 20 = 125.0
        self.assertEqual(df.loc[2020, "Owner_Earnings"], 125.0)

        # 2021: net_profit(120) + da(20) + impairment_charges(0) - fair_value_changes(30) - maintenance_capex(20)
        # = 120 + 20 + 0 - 30 - 20 = 90.0
        self.assertEqual(df.loc[2021, "Owner_Earnings"], 90.0)

    def test_goodwill_and_ma_ratios(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: goodwill=10, total_equity=500, Invested_Capital=600 (from existing test), OCF=130, ma_paid=5
        self.assertAlmostEqual(df.loc[2020, "Goodwill_to_Equity"], 10 / 500)
        self.assertAlmostEqual(df.loc[2020, "Goodwill_to_IC"], 10 / 600)
        self.assertAlmostEqual(df.loc[2020, "MA_to_OCF"], 5 / 130)

    def test_earnings_quality_metrics(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: OCF=130, capex=40 -> FCF=90; net_profit=100 -> FCF/NI=0.9
        self.assertEqual(df.loc[2020, "FCF"], 90)
        self.assertAlmostEqual(df.loc[2020, "FCF_to_NetIncome"], 90 / 100)
        # Owner_Earnings 2020 = 100 + 20 - 20 = 100; OE/NI = 1.0
        self.assertAlmostEqual(df.loc[2020, "OE_to_NetProfit"], 100 / 100)
        # Accruals = (net_profit - OCF) / IC = (100 - 130) / 600 = -30/600
        self.assertAlmostEqual(df.loc[2020, "Accruals_Ratio"], (100 - 130) / 600)
        # OEPS = Owner_Earnings / shares_in_millions = 100 / 100 = 1.0
        self.assertAlmostEqual(df.loc[2020, "OEPS"], 100 / 100)

    def test_acquisition_roiic_in_processed_df(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        self.assertIn("Acquisition_ROIIC_3Y", df.columns)
        self.assertIn("Acquisition_ROIIC_5Y", df.columns)
        self.assertIn("Goodwill_vs_NOPAT_Growth_5Y", df.columns)

        # Acquisition ROIIC mirrors ROIIC_Retained structure: with lag=1 and ma_paid=5 each year,
        # at 2023 (window=3): NOPAT diff = NOPAT(2023)-NOPAT(2020); cumulative ma (lag 1) = 5*3 = 15
        # NOPAT 2020 = 120*0.8=96, NOPAT 2023 = 210*0.8=168 -> diff=72; 72/15 = 4.8
        self.assertAlmostEqual(df.loc[2023, "Acquisition_ROIIC_3Y"], 72 / 15)

    def test_acquisition_roiic_zero_ma_returns_nan(self):
        sample = make_sample_input()
        sample.financials.ma_paid = [0.0] * 6
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        # With zero M&A spend, cumulative_ma denominator is never positive -> all NaN
        self.assertTrue(df["Acquisition_ROIIC_3Y"].dropna().empty)

    def test_optimized_invested_capital_and_average_roic(self):
        sample = make_sample_input()
        sample.financials.short_term_deposits = [100.0, 50.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.time_deposits_non_current = [50.0, 30.0, 0.0, 0.0, 0.0, 0.0]
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: total_equity(500) + debt(150) - cash_and_equiv(50) - short_term_deposits(100) - time_deposits_non_current(50) = 450
        self.assertEqual(df.loc[2020, "Invested_Capital"], 450.0)

        # 2021: total_equity(550) + debt(150) - cash_and_equiv(50) - short_term_deposits(50) - time_deposits_non_current(30) = 570
        self.assertEqual(df.loc[2021, "Invested_Capital"], 570.0)

        # 2021 average IC: (450 + 570) / 2 = 510
        # 2021 NOPAT: EBIT(150) * (1 - 0.2) = 120
        # 2021 ROIC: 120 / 510 = 0.235294...
        self.assertAlmostEqual(df.loc[2021, "ROIC"], 120.0 / 510.0)

    def test_capital_light_expansion_returns_inf(self):
        sample = make_sample_input()
        sample.financials.dividends_paid = [100, 120, 140, 160, 180, 200]
        sample.financials.buybacks_paid = [0, 0, 0, 0, 0, 0]

        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        # In 2023, window=3, lag=1: cumulative retained for 2020+2021+2022 is 0.
        # NOPAT grows from 96 (2020) to 168 (2023), so nopat_diff = 72 > 0.
        # Expected value is np.inf
        self.assertEqual(df.loc[2023, "ROIIC_Retained_3Y"], np.inf)

    def test_negative_invested_capital_yields_infinite_roic(self):
        sample = make_sample_input()
        # Set short-term investments extremely high to drive Invested_Capital negative
        # total_equity(500) + debt(150) - short_term_investment(1000) = -350
        sample.financials.short_term_investment = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0]

        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df

        # Invested capital must be negative
        self.assertLess(df.loc[2020, "Invested_Capital"], 0)
        # NOPAT is positive
        self.assertGreater(df.loc[2020, "NOPAT"], 0)
        # ROIC must be positive infinity
        self.assertEqual(df.loc[2020, "ROIC"], np.inf)


if __name__ == "__main__":
    unittest.main()
