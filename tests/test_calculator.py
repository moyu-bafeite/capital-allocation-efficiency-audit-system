import unittest

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


if __name__ == "__main__":
    unittest.main()
