"""Unit tests for the HKEX .doc parser module (pure parsing, no network).

Fixtures are derived from real HKEX monthly-return .doc files (00837 譚木匠,
2014-12 and 2018-11 reports). The .doc files are binary OLE2 Word documents
whose form text is recoverable via latin-1 decode + BEL→space normalization
(see ``hkex_doc_parser._extract_doc_text``). Tests exercise both the full
``parse_share_capital_doc`` entry point (from a synthetic .doc blob that
decodes to the fixture text) and the individual legacy-parsing helpers it
reuses.
"""
import unittest
from datetime import date

from datalayer.providers.hkex_doc_parser import (
    _extract_doc_text,
    parse_share_capital_doc,
)
from datalayer.providers.hkex_pdf_parser import (
    _parse_report_period_legacy,
    _parse_section_ii_legacy,
)


# ----------------------------------------------------------------------
# Real .doc text fixtures (post _extract_doc_text: latin-1 + BEL→space)
# Extracted from 00837 譚木匠 .doc files downloaded during investigation.
# ----------------------------------------------------------------------

# 00837, report 2014-12-31, ordinary shares 250,000,000
PERIOD_LINE_2014 = "For the month ended (dd/mm/yyyy) :   31/12/2014"
SECTION_II_2014 = (
    "II. Movements in Issued Share Capital\r"
    " No. of ordinary shares No of preference shares No. of other classes of shares"
    "   (1) (2)    Balance at close of preceding month   250,000,000"
    "            N/A            N/A           N/A   "
    "Increase/ (decrease) during the month                NIL"
    "            N/A            N/A           N/A   "
    "Balance at close of the month  250,000,000"
    "            N/A            N/A           N/A      \r"
)

# 00837, report 2018-11-30, ordinary shares 248,714,000
PERIOD_LINE_2018 = "For the month ended (dd/mm/yyyy) :   30/11/2018"
SECTION_II_2018 = (
    "II. Movements in Issued Share Capital\r"
    " No. of ordinary shares No of preference shares No. of other classes of shares"
    "   (1) (2)    Balance at close of preceding month   248,714,000"
    "            N/A            N/A           N/A   "
    "Increase/ (decrease) during the month                 NIL"
    "            N/A            N/A           N/A   "
    "Balance at close of the month  248,714,000"
    "            N/A            N/A           N/A      \r"
)

# A full .doc-like text blob: report period + Section I (authorised, must be
# ignored) + Section II (issued, the target) + trailing III. We keep form
# keywords as plain ASCII (as pypdf/Word would emit) and inject a couple of
# BEL chars only around cell numbers to mimic real .doc table formatting —
# this verifies _extract_doc_text's BEL→space normalization without breaking
# the regexes that scan for English headings.
_DOC_TEXT_2014 = (
    "Monthly Return of Equity Issuer on Movements in Securities\r"
    + PERIOD_LINE_2014
    + "\rTo : Hong Kong Exchanges and Clearing Limited\r"
    + "Name of Issuer 譚木匠\r"
    + "I. Movements in Authorised Share Capital\r"
    + "Balance at close of the month\x07 50,000,000,000\r"  # authorised, NOT issued
    + SECTION_II_2014
    + "\rIII. Details of Movements in Issued Share Capital\r"
)
_DOC_BYTES_2014 = _DOC_TEXT_2014.encode("latin-1", errors="ignore")


class ExtractDocTextTest(unittest.TestCase):
    def test_latin1_decode_and_bel_normalize(self):
        # A small blob with a BEL char and non-ASCII byte. After normalization
        # the BEL becomes a space and the form marker survives intact.
        raw = b"Name\x07Balance at close of the month\x07 250,000,000\xff"
        text = _extract_doc_text(raw)
        self.assertNotIn("\x07", text)
        self.assertIn("Balance at close of the month", text)
        self.assertIn("250,000,000", text)
        # \xff decodes as latin-1 ÿ — tolerated, does not crash.
        self.assertIn("\xff", text)

    def test_non_ascii_ignored(self):
        # Bytes that are non-ASCII should not crash extraction; parsing only
        # relies on ASCII form fields.
        text = _extract_doc_text(b"\xff\xfe For the month ended")
        self.assertIn("For the month ended", text)


class ParseReportPeriodLegacyTest(unittest.TestCase):
    def test_2014_december(self):
        self.assertEqual(_parse_report_period_legacy(PERIOD_LINE_2014), date(2014, 12, 31))

    def test_2018_november(self):
        self.assertEqual(_parse_report_period_legacy(PERIOD_LINE_2018), date(2018, 11, 30))


class ParseSectionIiLegacyTest(unittest.TestCase):
    def test_2014_ordinary_shares(self):
        issued, treasury, total = _parse_section_ii_legacy(SECTION_II_2014)
        self.assertEqual(total, 250000000)
        self.assertEqual(issued, 250000000)
        self.assertEqual(treasury, 0)

    def test_2018_ordinary_shares(self):
        issued, treasury, total = _parse_section_ii_legacy(SECTION_II_2018)
        self.assertEqual(total, 248714000)
        self.assertEqual(issued, 248714000)
        self.assertEqual(treasury, 0)

    def test_does_not_match_authorised_capital_only(self):
        # A blob with only Section I "Balance at close" (authorised) and no
        # Section II heading must not yield a false positive.
        bad = "I. Movements in Authorised Share Capital\rBalance at close of the month 50,000,000,000\r"
        issued, treasury, total = _parse_section_ii_legacy(bad)
        # The legacy regex would match this number, but parse_share_capital_doc
        # scopes parsing to the Section II block only (tested below).
        # Here we just confirm the regex itself matches the authorised number —
        # isolation is the caller's job, verified in the integration test.
        self.assertEqual(total, 50000000000)


class ParseShareCapitalDocIntegrationTest(unittest.TestCase):
    """End-to-end: parse_share_capital_doc from a synthetic .doc bytes blob."""

    def test_full_parse_2014(self):
        rec = parse_share_capital_doc(
            _DOC_BYTES_2014, "00837", "譚木匠",
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2015/0106/ltn201501061454.doc",
        )
        self.assertIsNotNone(rec)
        self.assertEqual(rec["stock_code"], "00837")
        self.assertEqual(rec["company_name"], "譚木匠")
        self.assertEqual(rec["report_period_date"], date(2014, 12, 31))
        self.assertEqual(rec["report_year"], 2014)
        self.assertEqual(rec["report_month"], 12)
        self.assertEqual(rec["shares_issued_excl_treasury"], 250000000)
        self.assertEqual(rec["shares_treasury"], 0)
        self.assertEqual(rec["shares_total_issued"], 250000000)
        # ltn-prefixed URL → pub_date None (pre-existing behavior)
        self.assertIsNone(rec["pub_date"])
        self.assertTrue(rec["source_pdf_url"].endswith(".doc"))

    def test_full_parse_isolates_section_ii_from_authorised(self):
        # The synthetic blob contains a Section I "Balance at close 50,000,000,000"
        # (authorised capital) that must NOT be picked up — only the Section II
        # ordinary count (250,000,000) should be returned.
        rec = parse_share_capital_doc(
            _DOC_BYTES_2014, "00837", "譚木匠",
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2015/0106/ltn201501061454.doc",
        )
        self.assertEqual(rec["shares_total_issued"], 250000000)
        self.assertNotEqual(rec["shares_total_issued"], 50000000000)

    def test_missing_section_ii_returns_none(self):
        bad = b"No Section II here at all"
        self.assertIsNone(parse_share_capital_doc(bad, "00837", "X", "http://x/y.doc"))

    def test_missing_report_period_returns_none(self):
        # Has Section II heading but no report period line.
        bad = ("Name of Issuer\r" + SECTION_II_2014).encode("latin-1", errors="ignore")
        self.assertIsNone(parse_share_capital_doc(bad, "00837", "X", "http://x/y.doc"))

    def test_unparseable_section_ii_returns_none(self):
        # Has report period and Section II heading but no Balance line in block.
        bad = (
            PERIOD_LINE_2014 + "\r"
            + "II. Movements in Issued Share Capital\r"
            + "garbage without any balance line\r"
            + "III. Details\r"
        ).encode("latin-1", errors="ignore")
        self.assertIsNone(parse_share_capital_doc(bad, "00837", "X", "http://x/y.doc"))


if __name__ == "__main__":
    unittest.main()
