import unittest

from models.input_schema import CompanyAuditInput
from tests.test_calculator import make_sample_input


class InputSchemaTest(unittest.TestCase):
    def test_valid_sample_input_passes(self):
        data = make_sample_input()
        self.assertEqual(data.ticker, "TEST")

    def test_years_must_be_strictly_increasing(self):
        raw = make_sample_input().model_dump()
        raw["years"] = [2020, 2021, 2021, 2023, 2024, 2025]

        with self.assertRaises(ValueError):
            CompanyAuditInput(**raw)

    def test_buyback_paid_requires_buyback_shares(self):
        raw = make_sample_input().model_dump()
        raw["financials"]["buybacks_paid"][2] = 10
        raw["financials"]["buybacks_shares"][2] = 0

        with self.assertRaises(ValueError):
            CompanyAuditInput(**raw)

    def test_optional_fields_initialization_to_zero(self):
        raw = make_sample_input().model_dump()
        data = CompanyAuditInput(**raw)
        self.assertIsNotNone(data.financials.special_items_of_operating_profit)
        self.assertEqual(data.financials.special_items_of_operating_profit, [0.0] * len(data.years))
        self.assertEqual(data.financials.short_term_deposits, [0.0] * len(data.years))
        self.assertEqual(data.financials.lease_liability_current, [0.0] * len(data.years))
        self.assertEqual(data.financials.lease_liability_non_current, [0.0] * len(data.years))
        self.assertEqual(data.financials.convertible_bonds, [0.0] * len(data.years))
        self.assertEqual(data.financials.notes_payable, [0.0] * len(data.years))
        self.assertEqual(data.financials.cashflow_impairment_adjustment, [0.0] * len(data.years))
        self.assertEqual(data.financials.cashflow_fair_value_adjustment, [0.0] * len(data.years))
        self.assertEqual(data.financials.income_impairment_charges, [0.0] * len(data.years))
        self.assertEqual(data.financials.income_fair_value_changes, [0.0] * len(data.years))
        self.assertEqual(data.financials.operating_interest_expense, [0.0] * len(data.years))
        self.assertEqual(data.financials.share_of_profit_associates, [0.0] * len(data.years))
        self.assertEqual(data.financials.share_of_profit_joint_venture, [0.0] * len(data.years))


if __name__ == "__main__":
    unittest.main()
