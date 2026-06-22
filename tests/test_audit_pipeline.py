import unittest

import pandas as pd

from core.buyback_audit import audit_buybacks
from core.checklist import generate_checklist
from core.valuation import calculate_intrinsic_value
from services.audit_pipeline import AuditParams, run_audit
from tests.test_calculator import make_sample_input


class AuditModulesTest(unittest.TestCase):
    def test_dcf_intrinsic_value_uses_two_stage_model(self):
        df = pd.DataFrame(
            {
                "Owner_Earnings": [100],
                "shares_outstanding": [100 * 1e6],
            },
            index=[2020],
        )
        series = calculate_intrinsic_value(
            df,
            wacc=0.10,
            growth_stage_1=0.0,
            stage_1_years=1,
            growth_stage_2=0.0,
            stage_2_years=1,
            terminal_growth=0.02,
            amount_unit="million",
        )

        expected = (100 / 1.10 + 100 / (1.10**2) + (102 / 0.08) / (1.10**2)) / 100
        self.assertAlmostEqual(series.loc[2020], expected)

    def test_dcf_rejects_invalid_terminal_growth(self):
        df = pd.DataFrame({"Owner_Earnings": [100], "shares_outstanding": [100 * 1e6]}, index=[2020])

        with self.assertRaises(ValueError):
            calculate_intrinsic_value(df, wacc=0.03, terminal_growth=0.03, amount_unit="million")

    def test_buyback_audit_rates_discounted_buybacks_as_excellent(self):
        df = pd.DataFrame(
            {
                "buybacks_paid": [10],
                "buybacks_shares": [1 * 1e6],
                "Intrinsic_Value_Share": [20],
            },
            index=[2020],
        )

        audited_df = audit_buybacks(df)
        self.assertEqual(audited_df.loc[2020, "Buyback_to_Intrinsic_Ratio"], 0.5)
        self.assertIn("卓越", audited_df.loc[2020, "Buyback_Audit_Rating"])

    def test_checklist_generates_six_principles(self):
        df = pd.DataFrame(
            {
                "ROIC": [0.15, 0.16],
                "ROIIC_Retained_3Y": [0.3, 0.3],
                "ROIIC_Retained_5Y": [0.06, 0.06],
                "One_Dollar_Rule_5Y": [1.2, 1.2],
                "Buyback_to_Intrinsic_Ratio": [pd.NA, pd.NA],
                "buybacks_paid": [0, 0],
                "dividends_paid": [10, 10],
                "Owner_Earnings": [100, 100],
                "net_profit": [100, 100],
                "operating_cash_flow": [120, 120],
                "capex": [20, 20],
            }
        )

        checklist = generate_checklist(df, wacc=0.08)
        self.assertEqual(len(checklist["principles"]), 6)
        self.assertEqual(checklist["roiic_col"], "ROIIC_Retained_5Y")
        self.assertIn("pass_count", checklist)
        self.assertIn("summary", checklist)

    def test_pipeline_returns_complete_audited_dataframe(self):
        result = run_audit(
            make_sample_input(),
            AuditParams(
                maintenance_capex_ratio=0.5,
                roiic_window_1=3,
                roiic_window_2=5,
                roiic_retained_lag=1,
                wacc=0.08,
                growth_stage_1=0.02,
                growth_stage_2=0.01,
                terminal_growth=0.01,
            ),
        )

        self.assertIn("Intrinsic_Value_Share", result.audited_df.columns)
        self.assertIn("Buyback_Audit_Rating", result.audited_df.columns)
        self.assertEqual(result.checklist["roiic_col"], "ROIIC_Retained_5Y")
        self.assertEqual(len(result.checklist["principles"]), 6)


if __name__ == "__main__":
    unittest.main()
