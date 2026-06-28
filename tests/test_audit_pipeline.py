import unittest

import pandas as pd

from core.buyback_audit import audit_buybacks
from core.checklist import generate_checklist
from core.valuation import calculate_intrinsic_value
from services.audit_pipeline import AuditParams, run_audit
from tests.test_calculator import make_sample_input
from i18n import Translatable


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

    def test_dcf_vectorization_multiple_rows_and_invalid_values(self):
        df = pd.DataFrame(
            {
                "Owner_Earnings": [100.0, 0.0, -50.0, 150.0, 120.0, None],
                "shares_outstanding": [100.0 * 1e6, 50.0 * 1e6, 50.0 * 1e6, 0.0, -10.0 * 1e6, 100.0 * 1e6],
            },
            index=[2020, 2021, 2022, 2023, 2024, 2025],
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

        expected_2020 = (100 / 1.10 + 100 / (1.10**2) + (102 / 0.08) / (1.10**2)) / 100
        self.assertAlmostEqual(series.loc[2020], expected_2020)

        import numpy as np
        self.assertTrue(np.isnan(series.loc[2021]))
        self.assertTrue(np.isnan(series.loc[2022]))
        self.assertTrue(np.isnan(series.loc[2023]))
        self.assertTrue(np.isnan(series.loc[2024]))
        self.assertTrue(np.isnan(series.loc[2025]))

    def test_dcf_no_division_by_zero_warnings(self):
        import warnings
        df = pd.DataFrame(
            {
                "Owner_Earnings": [100.0, 150.0],
                "shares_outstanding": [0.0, 100.0 * 1e6],
            },
            index=[2020, 2021],
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            series = calculate_intrinsic_value(df, wacc=0.10, amount_unit="million")
            
            for warning in w:
                self.assertNotIn("divide by zero", str(warning.message))
                self.assertNotIn("invalid value", str(warning.message))

        self.assertTrue(pd.isna(series.loc[2020]))
        self.assertFalse(pd.isna(series.loc[2021]))

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
        self.assertEqual(audited_df.loc[2020, "Buyback_Audit_Rating"], "excellent")

    def test_checklist_generates_eight_principles(self):
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
        self.assertEqual(len(checklist["principles"]), 8)
        self.assertEqual(checklist["roiic_col"], "ROIIC_Retained_5Y")
        self.assertIn("pass_count", checklist)
        self.assertIn("summary", checklist)
        self.assertIsInstance(checklist["summary"], Translatable)
        self.assertEqual(checklist["summary"].key, "checklist.summary")

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
        self.assertEqual(len(result.checklist["principles"]), 8)

    def test_infinite_roic_in_checklist_principles(self):
        import numpy as np
        df = pd.DataFrame(
            {
                "ROIC": [np.inf, np.inf],
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
        p1 = checklist["principles"][0]
        self.assertEqual(p1["status"], "pass")
        self.assertIsInstance(p1["value"], Translatable)
        self.assertEqual(p1["value"].key, "checklist.p1.value.negative_ic")
        self.assertIsInstance(p1["description"], Translatable)
        self.assertIn("checklist.p1.desc.money_printer", p1["description"].key)

        p2 = checklist["principles"][1]
        self.assertEqual(p2["status"], "fail")
        self.assertIsInstance(p2["benchmark"], Translatable)
        self.assertEqual(p2["benchmark"].key, "checklist.p2.benchmark.negative_ic")

        df_pass = df.copy()
        df_pass["ROIIC_Retained_5Y"] = [0.15, 0.15]
        checklist_pass = generate_checklist(df_pass, wacc=0.08)
        p2_pass = checklist_pass["principles"][1]
        self.assertEqual(p2_pass["status"], "pass")

        p6 = checklist["principles"][5]
        self.assertEqual(p6["status"], "pass")
        self.assertIsInstance(p6["value"], Translatable)
        self.assertEqual(p6["value"].key, "checklist.p6.value.sustained_inf")

        df_leap = df.copy()
        df_leap["ROIC"] = [0.15, np.inf]
        checklist_leap = generate_checklist(df_leap, wacc=0.08)
        p6_leap = checklist_leap["principles"][5]
        self.assertEqual(p6_leap["status"], "pass")
        self.assertIsInstance(p6_leap["value"], Translatable)
        self.assertEqual(p6_leap["value"].key, "checklist.p6.value.leap")
        self.assertAlmostEqual(p6_leap["value"].params["first_roic"], 0.15)

        df_slip = df.copy()
        df_slip["ROIC"] = [np.inf, 0.15]
        checklist_slip = generate_checklist(df_slip, wacc=0.08)
        p6_slip = checklist_slip["principles"][5]
        self.assertEqual(p6_slip["status"], "fail")
        self.assertIsInstance(p6_slip["value"], Translatable)
        self.assertEqual(p6_slip["value"].key, "checklist.p6.value.slip")
        self.assertAlmostEqual(p6_slip["value"].params["last_roic"], 0.15)

        df_p7 = df.copy()
        df_p7["ma_paid"] = [10.0, 10.0]
        df_p7["Acquisition_ROIIC_5Y"] = [0.06, 0.06]
        checklist_p7 = generate_checklist(df_p7, wacc=0.08)
        p7 = checklist_p7["principles"][6]
        self.assertEqual(p7["status"], "fail")
        self.assertNotIsInstance(p7["benchmark"], Translatable)
        self.assertEqual(p7["benchmark"], "WACC 8.0%")

        df_p7_pass = df_p7.copy()
        df_p7_pass["Acquisition_ROIIC_5Y"] = [0.15, 0.15]
        checklist_p7_pass = generate_checklist(df_p7_pass, wacc=0.08)
        p7_pass = checklist_p7_pass["principles"][6]
        self.assertEqual(p7_pass["status"], "pass")


if __name__ == "__main__":
    unittest.main()
