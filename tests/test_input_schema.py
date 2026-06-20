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
        raw["financials"]["buybacks_shares_m"][2] = 0

        with self.assertRaises(ValueError):
            CompanyAuditInput(**raw)


if __name__ == "__main__":
    unittest.main()
