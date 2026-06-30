import os
import shutil
import tempfile
import unittest
from datetime import date
from typing import Any, Dict

from hkex_app.store import HkexShareCapitalStore


def _record(stock_code: str, period: date, total: int,
            treasury: int = 0, company_name: str = "Test Co",
            pub_date: date = None) -> Dict[str, Any]:
    """Build a minimal record matching the schema expected by save_hkex_share_capital."""
    return {
        "stock_code": stock_code,
        "company_name": company_name,
        "report_period_date": period,
        "report_year": period.year,
        "report_month": period.month,
        "pub_date": pub_date or period,
        "shares_issued_excl_treasury": total - treasury,
        "shares_treasury": treasury,
        "shares_total_issued": total,
        "source_pdf_url": f"https://example/{stock_code}/{period}.pdf",
    }


class HkexShareCapitalStoreTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_hkex.db")
        self.store = HkexShareCapitalStore(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _seed(self, stock_code: str, periods, total_base: int = 1_000_000):
        for i, p in enumerate(periods):
            self.store.save_hkex_share_capital(
                _record(stock_code, p, total_base + i * 1000)
            )

    # ── inherited behavior still works ────────────────────────────────
    def test_inherited_save_and_latest_pub_date(self):
        self.store.save_hkex_share_capital(
            _record("00700", date(2024, 1, 31), 1_000_000, pub_date=date(2024, 2, 5))
        )
        self.store.save_hkex_share_capital(
            _record("00700", date(2024, 2, 29), 1_001_000, pub_date=date(2024, 3, 5))
        )
        latest = self.store.get_latest_hkex_pub_date("00700")
        self.assertEqual(latest, date(2024, 3, 5))

    # ── list_hkex_stock_codes ─────────────────────────────────────────
    def test_list_stock_codes_dedup_and_count(self):
        self._seed("00700", [date(2024, 1, 31), date(2024, 2, 29)])
        self._seed("00005", [date(2024, 1, 31)])
        rows = self.store.list_hkex_stock_codes()
        codes = [r["stock_code"] for r in rows]
        self.assertEqual(codes, ["00005", "00700"])  # ordered by stock_code
        r700 = next(r for r in rows if r["stock_code"] == "00700")
        self.assertEqual(r700["records"], 2)
        self.assertEqual(r700["company_name"], "Test Co")

    def test_list_stock_codes_empty(self):
        self.assertEqual(self.store.list_hkex_stock_codes(), [])

    # ── get_hkex_share_capital_range ──────────────────────────────────
    def test_range_filters_by_date(self):
        self._seed("00700", [
            date(2023, 12, 31), date(2024, 1, 31), date(2024, 2, 29),
            date(2024, 3, 31), date(2025, 1, 31),
        ])
        recs = self.store.get_hkex_share_capital_range(
            "00700", date(2024, 1, 1), date(2024, 12, 31)
        )
        periods = [r["report_period_date"] for r in recs]
        self.assertEqual(periods, [date(2024, 1, 31), date(2024, 2, 29), date(2024, 3, 31)])

    def test_range_open_bounds(self):
        self._seed("00700", [date(2024, 1, 31), date(2024, 2, 29)])
        # No bounds → all records
        all_recs = self.store.get_hkex_share_capital_range("00700")
        self.assertEqual(len(all_recs), 2)
        # Only start
        start_only = self.store.get_hkex_share_capital_range(
            "00700", start=date(2024, 2, 1)
        )
        self.assertEqual(len(start_only), 1)
        self.assertEqual(start_only[0]["report_period_date"], date(2024, 2, 29))
        # Only end
        end_only = self.store.get_hkex_share_capital_range(
            "00700", end=date(2024, 1, 31)
        )
        self.assertEqual(len(end_only), 1)
        self.assertEqual(end_only[0]["report_period_date"], date(2024, 1, 31))

    def test_range_unknown_stock_returns_empty(self):
        self.assertEqual(self.store.get_hkex_share_capital_range("99999"), [])

    def test_range_ordered_ascending(self):
        self._seed("00700", [date(2024, 3, 31), date(2024, 1, 31), date(2024, 2, 29)])
        recs = self.store.get_hkex_share_capital_range("00700")
        periods = [r["report_period_date"] for r in recs]
        self.assertEqual(periods, sorted(periods))

    # ── get_hkex_year_range ───────────────────────────────────────────
    def test_year_range(self):
        self._seed("00700", [
            date(2022, 12, 31), date(2023, 6, 30), date(2024, 1, 31),
        ])
        lo, hi = self.store.get_hkex_year_range("00700")
        self.assertEqual((lo, hi), (2022, 2024))

    def test_year_range_no_records(self):
        self.assertEqual(self.store.get_hkex_year_range("00700"), (None, None))

    # ── delete_hkex_share_capital ─────────────────────────────────────
    def test_delete_single_record(self):
        self._seed("00700", [date(2024, 1, 31), date(2024, 2, 29)])
        deleted = self.store.delete_hkex_share_capital("00700", date(2024, 1, 31))
        self.assertTrue(deleted)
        remaining = self.store.get_hkex_share_capital_range("00700")
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["report_period_date"], date(2024, 2, 29))

    def test_delete_nonexistent_returns_false(self):
        deleted = self.store.delete_hkex_share_capital("00700", date(2099, 1, 31))
        self.assertFalse(deleted)

    # ── delete_hkex_share_capital_stock ───────────────────────────────
    def test_clear_stock_deletes_all_and_returns_count(self):
        self._seed("00700", [date(2024, 1, 31), date(2024, 2, 29), date(2024, 3, 31)])
        self._seed("00005", [date(2024, 1, 31)])
        n = self.store.delete_hkex_share_capital_stock("00700")
        self.assertEqual(n, 3)
        self.assertEqual(self.store.get_hkex_share_capital_range("00700"), [])
        # Other ticker untouched
        self.assertEqual(len(self.store.get_hkex_share_capital_range("00005")), 1)

    def test_clear_unknown_stock_returns_zero(self):
        self.assertEqual(self.store.delete_hkex_share_capital_stock("99999"), 0)


if __name__ == "__main__":
    unittest.main()
