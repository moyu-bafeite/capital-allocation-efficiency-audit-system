"""Unit tests for the hkex_sync.py dry-run table rendering (Pass/Failed + Reason).

Pure-function tests over ``_format_records_table`` — no network, no DB. Uses
synthetic pass and fail record dicts to verify the merged table contains the
Status and Reason columns, renders "—" for missing numeric fields on failed
rows, and sorts by report_period_date ascending.
"""
import os
import sys
import unittest
from datetime import date

# Make project root importable so scripts.hkex_sync can be imported as a module.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# scripts/hkex_sync.py is a CLI script, not a package module. Import it by path
# to avoid triggering its argparse __main__ guard.
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "hkex_sync", os.path.join(_PROJECT_ROOT, "scripts", "hkex_sync.py"),
)
hkex_sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hkex_sync)
_format_records_table = hkex_sync._format_records_table


def _pass_rec(period, total, pub=None, month=None):
    return {
        "stock_code": "00700",
        "company_name": "Tencent",
        "report_period_date": period,
        "report_year": period.year,
        "report_month": month if month is not None else period.month,
        "pub_date": pub,
        "shares_issued_excl_treasury": total,
        "shares_treasury": 0,
        "shares_total_issued": total,
        "source_pdf_url": f"https://x/{period}.pdf",
    }


def _fail_rec(period, url, error, month=None):
    return {
        "stock_code": "00700",
        "company_name": "Tencent",
        "source_pdf_url": url,
        "report_period_date": period,
        "report_month": month,
        "error": error,
    }


class FormatRecordsTableTest(unittest.TestCase):
    def test_only_passes(self):
        recs = [_pass_rec(date(2024, 1, 31), 9431783365),
                _pass_rec(date(2024, 2, 29), 9431783365)]
        out = _format_records_table(recs, [], "00700", "Tencent")
        self.assertIn("2 pass", out)
        self.assertIn("0 failed", out)
        self.assertIn("Pass", out)
        self.assertNotIn("Failed", out)
        # Reason column header present but empty on pass rows
        self.assertIn("Reason", out)

    def test_only_failures(self):
        fails = [_fail_rec(date(2024, 1, 31), "https://x/a.pdf", "parse returned None")]
        out = _format_records_table([], fails, "00700", "Tencent")
        self.assertIn("0 pass", out)
        self.assertIn("1 failed", out)
        self.assertIn("Failed", out)
        self.assertIn("parse returned None", out)
        # Numeric columns show "—" on failed rows
        self.assertIn("—", out)

    def test_mixed_pass_and_fail_interleave_by_date(self):
        recs = [_pass_rec(date(2024, 2, 29), 9431783365, pub=date(2024, 3, 6))]
        fails = [_fail_rec(date(2024, 1, 31), "https://x/a.pdf", "bad PDF")]
        out = _format_records_table(recs, fails, "00700", "Tencent")
        self.assertIn("1 pass", out)
        self.assertIn("1 failed", out)
        # The failed row (Jan 31) should appear before the pass row (Feb 29)
        # since sorting is by report_period_date ascending.
        idx_fail = out.find("Failed")
        idx_pass = out.find("Pass")
        # "Pass" appears in the header row AND the pass data row; find the data
        # row by locating the share count that only pass rows carry.
        idx_pass_data = out.find("9,431,783,365")
        self.assertLess(idx_fail, idx_pass_data)
        self.assertIn("bad PDF", out)

    def test_failure_with_none_period_sorts_last(self):
        recs = [_pass_rec(date(2024, 2, 29), 9431783365)]
        fails = [_fail_rec(None, "https://x/unknown.pdf", "no date in URL")]
        out = _format_records_table(recs, fails, "00700", "Tencent")
        # None-period failure sorts LAST (unknown date at the bottom).
        idx_none = out.find("no date in URL")
        idx_pass = out.find("9,431,783,365")
        self.assertLess(idx_pass, idx_none)
        self.assertIn("—", out)  # PeriodEnd renders "—" for None

    def test_empty_inputs(self):
        out = _format_records_table([], [], "00700", "Tencent")
        self.assertIn("0 pass", out)
        self.assertIn("0 failed", out)
        self.assertIn("(no records)", out)

    def test_company_name_in_caption(self):
        out = _format_records_table([_pass_rec(date(2024, 1, 31), 100)], [], "00700", "Tencent")
        self.assertIn("(Tencent)", out)

    def test_no_company_name(self):
        out = _format_records_table([_pass_rec(date(2024, 1, 31), 100)], [], "00700", "")
        self.assertNotIn("()", out)


if __name__ == "__main__":
    unittest.main()
