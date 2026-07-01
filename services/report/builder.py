"""Audit report builder: assembles audit results into PDF or interactive HTML.

Public entry points:

* :func:`build_report` — PDF via WeasyPrint (archival/printable; needs system libs).
* :func:`build_report_html` — self-contained interactive HTML with embedded
  Plotly.js (zero system dependencies; charts are hoverable/zoomable).

Both consume the same trio the UI uses (``data``, ``params``, ``result``) and
share the same section builders. The only divergence is the chart rendering
step: PDF rasterizes figures to base64 PNG via kaleido; HTML embeds live
Plotly divs with the library inlined once in ``<head>``.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from i18n import LANGUAGE_LABELS, get_lang, resolve, t
from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult

from services.report.fonts import (
    get_html_serif_font_face_css,
    get_pdf_serif_font_face_css,
)
from services.report.renderer import (
    get_plotlyjs_inline,
    kaleido_server,
    safe_fig_to_base64_png,
    safe_fig_to_plotly_div,
)
from services.report.sections import (
    build_buyback_section,
    build_capital_allocation_section,
    build_checklist_section,
    build_earnings_quality_section,
    build_ledger_section,
    build_ma_goodwill_section,
    build_params_appendix,
    build_roic_roiic_section,
    _scale_absolute_to_million,
)
from services.report.template import render_html

logger = logging.getLogger(__name__)


def _safe_set_lang() -> str:
    """Activate the current session language (or default) and return its code."""
    return get_lang()


def _build_sections(
    data: CompanyAuditInput,
    params: AuditParams,
    effective_result: AuditResult,
    ledger_result: AuditResult = None,
) -> List[Dict[str, Any]]:
    """Build the seven body sections with format-agnostic chart figs.

    Sections emit ``{"fig": go.Figure, "height": int, ...}`` dicts; the
    format-specific rendering (PNG vs interactive div) happens later in
    :func:`_render_charts_for_pdf` / :func:`_render_charts_for_html`.

    ``ledger_result`` defaults to ``effective_result`` when omitted. When
    ``amount_unit == "absolute"``, the caller passes the *unscaled* result
    here so the ledger section mirrors the dashboard's
    ``section != SECTION_LEDGER`` exclusion (see
    :func:`ui.sections.render_selected_section`): the raw audit table keeps
    original absolute values while the other six sections render in
    million-scaled form.
    """
    if ledger_result is None:
        ledger_result = effective_result
    return [
        build_capital_allocation_section(data, effective_result),
        build_roic_roiic_section(params, effective_result),
        build_buyback_section(data, effective_result),
        build_ma_goodwill_section(data, params, effective_result),
        build_earnings_quality_section(data, effective_result),
        build_checklist_section(effective_result),
        build_ledger_section(data, ledger_result),
    ]


def _render_charts_for_pdf(sections: List[Dict[str, Any]]) -> None:
    """Mutate sections in place: replace ``fig`` with rasterized ``src`` (PNG).

    Wrapped in :func:`kaleido_server` to keep one Chromium instance alive
    across all charts (~5s total instead of ~90s).
    """
    with kaleido_server():
        for section in sections:
            for chart in section.get("charts", []):
                fig = chart.pop("fig", None)
                height = chart.get("height", 480)
                if fig is None:
                    continue
                src = safe_fig_to_base64_png(fig, height=height)
                if src:
                    chart["src"] = src
                else:
                    chart["src"] = None
                    chart["_failed"] = True


def _render_charts_for_html(sections: List[Dict[str, Any]]) -> None:
    """Mutate sections in place: replace ``fig`` with interactive ``html`` div."""
    for section in sections:
        for chart in section.get("charts", []):
            fig = chart.pop("fig", None)
            height = chart.get("height", 480)
            if fig is None:
                continue
            div = safe_fig_to_plotly_div(fig, height=height)
            if div:
                chart["html"] = div
            else:
                chart["html"] = None
                chart["_failed"] = True


def _build_context(
    data: CompanyAuditInput,
    params: AuditParams,
    result: AuditResult,
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    lang = _safe_set_lang()

    checklist = result.checklist
    counts = {
        "pass": checklist["pass_count"],
        "warning": checklist["warning_count"],
        "fail": checklist["fail_count"],
        "insufficient": checklist["insufficient_count"],
    }
    summary_text = resolve(checklist["summary"])

    years_range = f"{data.years[0]} - {data.years[-1]}"
    amount_unit_label = t("metric.unit.absolute") if data.amount_unit == "absolute" else data.amount_unit

    return {
        # Cover
        "eyebrow": t("app.nav_caption"),
        "report_title": t("app.title"),
        "company_name": data.company_name,
        "ticker": data.ticker,
        "years_range": years_range,
        "n_years": len(data.years),
        "currency": data.currency,
        "amount_unit_label": amount_unit_label,
        "market_currency": data.market_currency,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "language_label": LANGUAGE_LABELS.get(lang, lang),
        "lang": lang,
        "footer_note": (
            t("section.checklist.disclaimer1") + " " + t("section.checklist.disclaimer2")
        ),
        # Summary
        "sections_summary_title": t("section.nav.checklist"),
        "summary_intro": t("section.checklist.intro"),
        "summary_text": summary_text,
        "checklist_intro": _md_strip(t("section.checklist.intro")),
        "counts": counts,
        # Body
        "body_sections": sections,
        # Appendix
        "appendix_title": t("sidebar.params_header"),
        "appendix_intro": t("sidebar.params.section1").split(".")[0].lstrip("123. "),
        "params": build_params_appendix(params),
        "disclaimer_1": t("section.checklist.disclaimer1"),
        "disclaimer_2": t("section.checklist.disclaimer2"),
        # Labels shared with CSS @page boxes
        "labels": {
            "company": t("metric.label.company"),
            "years": t("metric.label.years"),
            "currency_unit": t("metric.label.currency_unit"),
            "market_currency": t("metric.label.market_currency"),
            "generated_at": "Generated At",
            "language": "Language",
            "pass": t("badge.pass"),
            "warning": t("badge.warning"),
            "fail": t("badge.fail"),
            "insufficient": t("badge.insufficient_data"),
            "param": "Parameter",
            "value": "Value",
        },
        # Plotly.js is injected only by the HTML path; PDF path leaves this None
        "plotly_js": None,
        # @font-face CSS is injected by both paths (local files for PDF, base64 for HTML)
        "font_face": None,
    }


def _md_strip(text: str) -> str:
    return (text or "").replace("**", "")


def build_report(
    data: CompanyAuditInput,
    params: AuditParams,
    result: AuditResult,
) -> bytes:
    """Build the full PDF audit report and return it as bytes.

    Raises:
        ImportError: if WeasyPrint is not installed.
        Exception: re-raised from WeasyPrint on rendering failure.
    """
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise ImportError(
            "weasyprint is required to build PDF reports. "
            "Install it via `pip install weasyprint` and install system deps "
            "(cairo, pango, gdk-pixbuf) — see README."
        ) from exc

    effective_result = (
        _scale_absolute_to_million(result)
        if data.amount_unit == "absolute"
        else result
    )
    sections = _build_sections(data, params, effective_result, ledger_result=result)
    _render_charts_for_pdf(sections)

    context = _build_context(data, params, result, sections)
    context["font_face"] = get_pdf_serif_font_face_css()
    html = render_html(context, mode="print")
    pdf_bytes = HTML(string=html, base_url=".").write_pdf()
    return pdf_bytes


def build_report_html(
    data: CompanyAuditInput,
    params: AuditParams,
    result: AuditResult,
) -> bytes:
    """Build a self-contained interactive HTML report and return it as bytes.

    The HTML embeds Plotly.js inline (~4.6 MB) so it works offline. Charts
    are live Plotly divs (hover/zoom/legend-toggle). Zero system dependencies
    beyond what Streamlit already requires.
    """
    effective_result = (
        _scale_absolute_to_million(result)
        if data.amount_unit == "absolute"
        else result
    )
    sections = _build_sections(data, params, effective_result, ledger_result=result)
    _render_charts_for_html(sections)

    context = _build_context(data, params, result, sections)
    context["font_face"] = get_html_serif_font_face_css()
    context["plotly_js"] = get_plotlyjs_inline()
    html = render_html(context, mode="screen")
    return html.encode("utf-8")
