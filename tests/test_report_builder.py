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


def _make_absolute_input():
    """Build a sample input with amount_unit='absolute' for scaling tests."""
    from models.input_schema import CompanyAuditInput, FinancialsSchema

    sample = make_sample_input()
    return CompanyAuditInput(
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


class RendererTest(unittest.TestCase):
    def test_fig_to_base64_png_returns_data_uri(self):
        from report.renderer import fig_to_base64_png

        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
        uri = fig_to_base64_png(fig, scale=1, height=200)

        self.assertIsInstance(uri, str)
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        payload = uri.split(",", 1)[1]
        self.assertGreater(len(payload), 100)

    def test_safe_fig_to_base64_png_returns_none_on_failure(self):
        from report.renderer import safe_fig_to_base64_png

        class BrokenFig:
            def to_image(self, **kwargs):
                raise RuntimeError("simulated kaleido failure")

            def update_layout(self, **kwargs):
                return self

        self.assertIsNone(safe_fig_to_base64_png(BrokenFig()))

    def test_fig_to_plotly_div_returns_interactive_html(self):
        from report.renderer import fig_to_plotly_div

        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
        div = fig_to_plotly_div(fig, height=240)

        self.assertIsInstance(div, str)
        self.assertIn("Plotly.newPlot", div)
        self.assertIn("<div", div)
        # Should NOT include the Plotly.js library itself (injected separately)
        self.assertNotIn("function plotly", div.lower())

    def test_safe_fig_to_plotly_div_returns_none_on_failure(self):
        from report.renderer import safe_fig_to_plotly_div

        class BrokenFig:
            def to_html(self, **kwargs):
                raise RuntimeError("simulated failure")

            def update_layout(self, **kwargs):
                return self

        self.assertIsNone(safe_fig_to_plotly_div(BrokenFig()))

    def test_get_plotlyjs_inline_is_substantial(self):
        from report.renderer import get_plotlyjs_inline

        js = get_plotlyjs_inline()
        self.assertIsInstance(js, str)
        # Plotly.js is ~4.6 MB; confirm we got the real library, not a stub
        self.assertGreater(len(js), 1_000_000)


class SectionsTest(unittest.TestCase):
    def setUp(self):
        self.data = make_sample_input()
        self.params = _make_params()
        self.result = run_audit(self.data, self.params)

    def test_capital_allocation_section_has_fig_charts(self):
        from report.sections import build_capital_allocation_section

        section = build_capital_allocation_section(self.data, self.result)
        self.assertIn("title", section)
        self.assertIn("charts", section)
        self.assertEqual(len(section["metrics"]), 4)
        # Charts now carry fig objects (format-agnostic), not src strings
        self.assertEqual(len(section["charts"]), 2)
        for chart in section["charts"]:
            self.assertIsInstance(chart["fig"], go.Figure)
            self.assertIn("height", chart)
            self.assertNotIn("src", chart)

    def test_all_sections_emit_fig_not_src(self):
        from report.sections import (
            build_buyback_section,
            build_earnings_quality_section,
            build_ma_goodwill_section,
            build_roic_roiic_section,
        )

        for builder, args in [
            (build_roic_roiic_section, (self.params, self.result)),
            (build_buyback_section, (self.data, self.result)),
            (build_ma_goodwill_section, (self.data, self.params, self.result)),
            (build_earnings_quality_section, (self.data, self.result)),
        ]:
            section = builder(*args)
            for chart in section.get("charts", []):
                self.assertIsInstance(chart["fig"], go.Figure)
                self.assertNotIn("src", chart)

    def test_buyback_section_table_has_year_column(self):
        from report.sections import build_buyback_section

        section = build_buyback_section(self.data, self.result)
        self.assertTrue(section["tables"])
        table = section["tables"][0]
        self.assertEqual(table["headers"][0], "Year")
        for row in table["rows"]:
            self.assertTrue(row[0].isdigit())

    def test_checklist_section_has_eight_principles(self):
        from report.sections import build_checklist_section

        section = build_checklist_section(self.result)
        self.assertEqual(len(section["principles"]), 8)
        for p in section["principles"]:
            self.assertIn(p["status"], ("pass", "fail", "warning", "insufficient_data"))
            self.assertIn("badge", p)

    def test_ledger_section_chunks_present(self):
        from report.sections import build_ledger_section

        section = build_ledger_section(self.data, self.result)
        self.assertTrue(section["tables"])
        for tbl in section["tables"]:
            self.assertEqual(len(tbl["headers"]), len(tbl["rows"][0]))

    def test_absolute_amount_unit_scaling(self):
        from report.sections import _scale_absolute_to_million

        abs_input = _make_absolute_input()
        result = run_audit(abs_input, _make_params())
        scaled = _scale_absolute_to_million(result)
        self.assertAlmostEqual(
            scaled.audited_df["net_profit"].iloc[0],
            result.audited_df["net_profit"].iloc[0] / 1e6,
        )

    def test_ledger_section_not_scaled_when_absolute(self):
        """Regression: when amount_unit=='absolute', the ledger Inputs table
        must show original absolute values (no /1e6 scaling), matching the
        dashboard's ``section != SECTION_LEDGER`` exclusion in
        :func:`ui.sections.render_selected_section`. Other sections must
        still receive million-scaled data.
        """
        from core.formatting import format_ledger_cell
        from report.builder import _build_sections
        from report.sections import (
            _scale_absolute_to_million,
            build_ma_goodwill_section,
        )

        abs_input = _make_absolute_input()
        result = run_audit(abs_input, _make_params())
        scaled = _scale_absolute_to_million(result)

        sections = _build_sections(
            abs_input, _make_params(), scaled, ledger_result=result
        )

        # _build_sections order: [capital, roic, buyback, ma, eq, checklist, ledger]
        ledger_section = sections[6]
        ma_section = sections[3]

        # 1) Ledger Inputs cells must equal formatting of the RAW (unscaled) result
        inputs_tbl = next(
            tbl for tbl in ledger_section["tables"] if tbl["caption"] == "Inputs"
        )
        np_idx = inputs_tbl["headers"].index("net_profit")
        ebit_idx = inputs_tbl["headers"].index("ebit")
        eq_idx = inputs_tbl["headers"].index("total_equity")
        for row_i, year in enumerate(result.audited_df.index):
            self.assertEqual(
                inputs_tbl["rows"][row_i][np_idx],
                format_ledger_cell(
                    result.audited_df.at[year, "net_profit"], "net_profit"
                ),
            )
            self.assertEqual(
                inputs_tbl["rows"][row_i][ebit_idx],
                format_ledger_cell(result.audited_df.at[year, "ebit"], "ebit"),
            )
            self.assertEqual(
                inputs_tbl["rows"][row_i][eq_idx],
                format_ledger_cell(
                    result.audited_df.at[year, "total_equity"], "total_equity"
                ),
            )

        # 2) Non-ledger section (M&A) must still use the SCALED result, not raw
        expected_scaled_ma = build_ma_goodwill_section(abs_input, _make_params(), scaled)
        expected_raw_ma = build_ma_goodwill_section(abs_input, _make_params(), result)
        self.assertEqual(ma_section["metrics"], expected_scaled_ma["metrics"])
        self.assertNotEqual(ma_section["metrics"], expected_raw_ma["metrics"])

    def test_format_ledger_cell_aligns_with_ui_rules(self):
        import numpy as np
        from core.formatting import format_ledger_cell

        # Ratio / price columns → 2 decimals
        self.assertEqual(format_ledger_cell(0.1234, "ROIC"), "0.12")
        self.assertEqual(format_ledger_cell(0.1234, "tax_rate"), "0.12")
        self.assertEqual(format_ledger_cell(9.876, "avg_stock_price"), "9.88")
        self.assertEqual(format_ledger_cell(1.234, "Intrinsic_Value_Share"), "1.23")
        # Quirk columns (no ratio/price keyword in name) → 2 decimals
        self.assertEqual(format_ledger_cell(0.1543, "Goodwill_to_Equity"), "0.15")
        self.assertEqual(format_ledger_cell(0.2345, "Goodwill_to_IC"), "0.23")
        self.assertEqual(format_ledger_cell(0.5678, "MA_to_OCF"), "0.57")
        self.assertEqual(format_ledger_cell(0.9, "OE_to_NetProfit"), "0.90")
        self.assertEqual(format_ledger_cell(0.8765, "FCF_to_NetIncome"), "0.88")
        self.assertEqual(format_ledger_cell(1.234, "OEPS"), "1.23")
        self.assertEqual(format_ledger_cell(0.0567, "Goodwill_vs_NOPAT_Growth_5Y"), "0.06")
        # Amount / share-count columns → 0 decimals with thousands sep
        self.assertEqual(format_ledger_cell(1234.6, "NOPAT"), "1,235")
        self.assertEqual(format_ledger_cell(1000.0, "Invested_Capital"), "1,000")
        self.assertEqual(format_ledger_cell(88.6, "shares_outstanding"), "89")
        # Short-circuits
        self.assertEqual(format_ledger_cell(np.nan, "ROIC"), "—")
        self.assertEqual(format_ledger_cell(np.inf, "ROIC"), "∞")
        self.assertEqual(format_ledger_cell("pass", "Buyback_Audit_Rating"), "pass")

    def test_ui_and_report_share_core_formatting(self):
        """Guard against drift: both layers must use core.formatting's helpers."""
        import core.formatting as fmt
        import ui.sections as ui_s
        import report.sections as rpt_s

        self.assertIs(ui_s.is_ratio_or_price_column, fmt.is_ratio_or_price_column)
        self.assertIs(rpt_s._format_ledger_cell, fmt.format_ledger_cell)

    def test_ledger_section_renders_quirk_columns_with_two_decimals(self):
        """End-to-end: the report ledger tables must format quirk ratio
        columns with 2 decimals (not the pre-fix 0-decimal `{:,.0f}`)."""
        import pandas as pd
        from report.sections import build_ledger_section

        section = build_ledger_section(self.data, self.result)
        df = self.result.audited_df
        # Find the ratios chunk and locate Goodwill_to_Equity column
        ratios_tbl = next(
            tbl for tbl in section["tables"] if tbl["caption"] == "Ratios"
        )
        col_idx = ratios_tbl["headers"].index("Goodwill_to_Equity")
        for row_idx, year in enumerate(df.index):
            raw = df.at[year, "Goodwill_to_Equity"]
            cell = ratios_tbl["rows"][row_idx][col_idx]
            if pd.notna(raw):
                # Two decimals implies the formatted string either has a
                # decimal point with two digits after it, or is "—"/"∞".
                self.assertIn(".", cell)
                self.assertEqual(len(cell.split(".")[-1]), 2)



class BuilderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = make_sample_input()
        cls.params = _make_params()
        cls.result = run_audit(cls.data, cls.params)

    def test_build_report_html_returns_bytes_with_plotly(self):
        from report import build_report_html

        payload = build_report_html(self.data, self.params, self.result)
        self.assertIsInstance(payload, bytes)
        self.assertEqual(payload[:9], b"<!DOCTYPE")
        # Interactive HTML path: must embed Plotly.newPlot calls
        self.assertIn(b"Plotly.newPlot", payload)
        # Plotly.js library inlined in <head> for offline use
        self.assertIn(b"function", payload)
        # Must contain key content
        self.assertIn(b"Test Company", payload)
        self.assertIn(b"TEST", payload)
        for i in range(1, 9):
            self.assertIn(f"Principle {i}".encode(), payload)

    def test_build_report_html_has_seven_body_sections(self):
        from report.builder import _build_sections, _build_context

        sections = _build_sections(self.data, self.params, self.result)
        ctx = _build_context(self.data, self.params, self.result, sections)
        self.assertEqual(len(ctx["body_sections"]), 7)
        for s in ctx["body_sections"]:
            self.assertTrue(s.get("title"))

    def test_build_report_html_absolute_unit(self):
        from report import build_report_html

        abs_input = _make_absolute_input()
        result = run_audit(abs_input, self.params)
        payload = build_report_html(abs_input, self.params, result)
        self.assertIn(b"Test Company", payload)
        self.assertIn(b"Plotly.newPlot", payload)

    def test_render_charts_for_pdf_replaces_fig_with_src(self):
        from report.builder import _build_sections, _render_charts_for_pdf

        sections = _build_sections(self.data, self.params, self.result)
        _render_charts_for_pdf(sections)
        for section in sections:
            for chart in section.get("charts", []):
                # After PDF rendering, fig is popped and src is set
                self.assertNotIn("fig", chart)
                self.assertIn("src", chart)

    def test_render_charts_for_html_replaces_fig_with_html_div(self):
        from report.builder import _build_sections, _render_charts_for_html

        sections = _build_sections(self.data, self.params, self.result)
        _render_charts_for_html(sections)
        for section in sections:
            for chart in section.get("charts", []):
                self.assertNotIn("fig", chart)
                self.assertIn("html", chart)
                if chart["html"]:
                    self.assertIn("Plotly.newPlot", chart["html"])

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
        # PDF path must not embed interactive Plotly
        self.assertNotIn(b"Plotly.newPlot", pdf)


if __name__ == "__main__":
    unittest.main()
