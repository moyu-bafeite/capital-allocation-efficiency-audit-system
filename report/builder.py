"""
PDF report builder: assembles audit results into a printable PDF.

Public entry point is :func:`build_report`, which accepts the same trio of
objects the UI consumes (``data``, ``params``, ``result``) and returns the
PDF as ``bytes`` ready for ``st.download_button``.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from i18n import LANGUAGES, LANGUAGE_LABELS, get_lang, resolve, t
from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult

from report.sections import (
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
from report.renderer import kaleido_server
from report.template import render_html

logger = logging.getLogger(__name__)


def _safe_set_lang() -> str:
    """Activate the current session language (or default) and return its code.

    ``get_lang`` already reads Streamlit session state; we just ensure the
    translations module uses the active language. Outside a Streamlit run
    (e.g. unit tests), it falls back to ``DEFAULT_LANG``.
    """
    return get_lang()


def _build_context(
    data: CompanyAuditInput,
    params: AuditParams,
    result: AuditResult,
) -> Dict[str, Any]:
    lang = _safe_set_lang()

    # Scale absolute-unit monetary fields to millions for display consistency
    effective_result = (
        _scale_absolute_to_million(result)
        if data.amount_unit == "absolute"
        else result
    )

    checklist = result.checklist
    counts = {
        "pass": checklist["pass_count"],
        "warning": checklist["warning_count"],
        "fail": checklist["fail_count"],
        "insufficient": checklist["insufficient_count"],
    }
    summary_text = resolve(checklist["summary"])

    # All chart rendering happens inside section builders; keep a single
    # kaleido Chromium instance alive across the whole batch to avoid the
    # ~15s per-chart subprocess startup tax.
    with kaleido_server():
        body_sections = [
            build_capital_allocation_section(data, effective_result),
            build_roic_roiic_section(params, effective_result),
            build_buyback_section(data, effective_result),
            build_ma_goodwill_section(data, params, effective_result),
            build_earnings_quality_section(data, effective_result),
            build_checklist_section(effective_result),
            build_ledger_section(data, effective_result),
        ]

    years_range = f"{data.years[0]} - {data.years[-1]}"
    amount_unit_label = t("metric.unit.absolute") if data.amount_unit == "absolute" else data.amount_unit

    return {
        # Cover
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
        "body_sections": body_sections,
        # Appendix
        "appendix_title": t("sidebar.params_header"),
        "appendix_intro": t("sidebar.params.section1").split(".")[0].lstrip("123. "),
        "params": build_params_appendix(params),
        "disclaimer_1": t("section.checklist.disclaimer1"),
        "disclaimer_2": t("section.checklist.disclaimer2"),
        # Labels shared with CSS @page boxes (kept simple)
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

    context = _build_context(data, params, result)
    html = render_html(context)
    pdf_bytes = HTML(string=html, base_url=".").write_pdf()
    return pdf_bytes


def build_report_html(
    data: CompanyAuditInput,
    params: AuditParams,
    result: AuditResult,
) -> str:
    """Build only the HTML (useful for debugging / previewing in a browser)."""
    context = _build_context(data, params, result)
    return render_html(context)
