import unittest

import plotly.graph_objects as go

from services.audit_pipeline import AuditParams, run_audit
from tests.test_calculator import make_sample_input


def _make_params() -> AuditParams:
    return AuditParams(
        maintenance_capex_ratio=0.5,
        roiic_window_1=3,
        roiic_window_2=5,
        roiic_retained_lag=1,
        wacc=0.08,
        growth_stage_1=0.02,
        growth_stage_2=0.01,
        terminal_growth=0.01,
    )


class RendererTest(unittest.TestCase):
    def test_fig_to_base64_png_returns_data_uri(self):
        from report.renderer import fig_to_base64_png

        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
        uri = fig_to_base64_png(fig, scale=1, height=200)

        self.assertIsInstance(uri, str)
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        # Base64 payload should be non-empty and decode cleanly
        payload = uri.split(",", 1)[1]
        self.assertGreater(len(payload), 100)

    def test_safe_fig_returns_none_on_failure(self):
        from report.renderer import safe_fig_to_base64_png

        # A figure with no traces and invalid layout won't crash to_image,
        # so feed something that will: a non-Figure object wrapped via
        # an attribute error path. Use a malformed figure by mocking.
        class BrokenFig:
            def to_image(self, **kwargs):
                raise RuntimeError("simulated kaleido failure")

            def update_layout(self, **kwargs):
                return self

        result = safe_fig_to_base64_png(BrokenFig())
        self.assertIsNone(result)


class SectionsTest(unittest.TestCase):
    def setUp(self):
        self.data = make_sample_input()
        self.params = _make_params()
        self.result = run_audit(self.data, self.params)

    def test_capital_allocation_section_structure(self):
        from report.sections import build_capital_allocation_section

        section = build_capital_allocation_section(self.data, self.result)
        self.assertIn("title", section)
        self.assertIn("charts", section)
        self.assertIn("metrics", section)
        self.assertEqual(len(section["metrics"]), 4)
        for m in section["metrics"]:
            self.assertIn("label", m)
            self.assertIn("value", m)

    def test_buyback_section_table_has_year_column(self):
        from report.sections import build_buyback_section

        section = build_buyback_section(self.data, self.result)
        self.assertTrue(section["tables"])
        table = section["tables"][0]
        self.assertEqual(table["headers"][0], "Year")
        # Each row should start with a year string
        for row in table["rows"]:
            self.assertTrue(row[0].isdigit())

    def test_checklist_section_has_eight_principles(self):
        from report.sections import build_checklist_section

        section = build_checklist_section(self.result)
        self.assertEqual(len(section["principles"]), 8)
        for p in section["principles"]:
            self.assertIn(p["status"], ("pass", "fail", "warning", "insufficient_data"))
            self.assertIn("badge", p)
            self.assertIn("title", p)
            self.assertIn("value", p)
            self.assertIn("benchmark", p)
            self.assertIn("description", p)

    def test_ledger_section_chunks_present(self):
        from report.sections import build_ledger_section

        section = build_ledger_section(self.data, self.result)
        # Expect at least the inputs chunk
        self.assertTrue(section["tables"])
        for tbl in section["tables"]:
            self.assertIn("headers", tbl)
            self.assertIn("rows", tbl)
            self.assertEqual(len(tbl["headers"]), len(tbl["rows"][0]))

    def test_absolute_amount_unit_scaling(self):
        from report.sections import _scale_absolute_to_million

        sample = make_sample_input()
        # Force absolute unit; values are in raw RMB so divide by 1e6 for display
        sample_financials = sample.financials
        # Build a result with absolute unit
        sample = make_sample_input()
        # Can't mutate frozen pydantic easily; re-create with absolute
        from models.input_schema import CompanyAuditInput, FinancialsSchema
        abs_input = CompanyAuditInput(
            ticker=sample.ticker,
            company_name=sample.company_name,
            currency=sample.currency,
            amount_unit="absolute",
            market_currency=sample.market_currency,
            exchange_rate_to_reporting_currency=sample.exchange_rate_to_reporting_currency,
            closing_exchange_rate_to_reporting_currency=sample.closing_exchange_rate_to_reporting_currency,
            years=sample.years,
            financials=FinancialsSchema(**sample.financials.model_dump()),
        )
        result = run_audit(abs_input, _make_params())
        scaled = _scale_absolute_to_million(result)
        # After scaling, net_profit in audited_df should be 1e6x smaller
        self.assertAlmostEqual(
            scaled.audited_df["net_profit"].iloc[0],
            result.audited_df["net_profit"].iloc[0] / 1e6,
        )


class BuilderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = make_sample_input()
        cls.params = _make_params()
        cls.result = run_audit(cls.data, cls.params)

    def test_build_report_html_contains_key_content(self):
        from report import build_report_html

        html = build_report_html(self.data, self.params, self.result)
        self.assertIn("<html", html)
        self.assertIn("Test Company", html)
        self.assertIn("TEST", html)
        # Should embed at least one base64 chart image
        self.assertIn("data:image/png;base64,", html)
        # Should contain all 8 principle titles
        for i in range(1, 9):
            self.assertIn(f"Principle {i}", html)

    def test_build_report_html_has_seven_body_sections(self):
        from report.builder import _build_context

        ctx = _build_context(self.data, self.params, self.result)
        self.assertEqual(len(ctx["body_sections"]), 7)
        # Each section must have a title
        for s in ctx["body_sections"]:
            self.assertTrue(s.get("title"))

    def test_build_report_html_absolute_unit(self):
        from report import build_report_html
        from models.input_schema import CompanyAuditInput, FinancialsSchema

        abs_input = CompanyAuditInput(
            ticker=self.data.ticker,
            company_name=self.data.company_name,
            currency=self.data.currency,
            amount_unit="absolute",
            market_currency=self.data.market_currency,
            exchange_rate_to_reporting_currency=self.data.exchange_rate_to_reporting_currency,
            closing_exchange_rate_to_reporting_currency=self.data.closing_exchange_rate_to_reporting_currency,
            years=self.data.years,
            financials=FinancialsSchema(**self.data.financials.model_dump()),
        )
        result = run_audit(abs_input, self.params)
        html = build_report_html(abs_input, self.params, result)
        self.assertIn("Test Company", html)
        self.assertIn("data:image/png;base64,", html)

    @unittest.skipUnless(
        __import__("importlib").util.find_spec("weasyprint"),
        "weasyprint not installed; skipping PDF rendering test",
    )
    def test_build_report_returns_valid_pdf_bytes(self):
        from report import build_report

        pdf = build_report(self.data, self.params, self.result)
        self.assertIsInstance(pdf, bytes)
        self.assertEqual(pdf[:5], b"%PDF-")
        self.assertGreater(len(pdf), 10000)


if __name__ == "__main__":
    unittest.main()
