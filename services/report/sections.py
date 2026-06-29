"""
Build section context dicts for the audit report template.

Each function mirrors the corresponding ``ui/sections.py`` render function
but returns plain data (dicts/lists) instead of issuing Streamlit calls.
The template in :mod:`report.template` consumes these structures.

Charts are emitted as ``{"fig": go.Figure, ...}`` dicts — format-agnostic.
The builder layer is responsible for rasterizing to PNG (PDF path) or
embedding an interactive Plotly div (HTML path).

The amount_unit=="absolute" scaling logic mirrors
:func:`ui.sections.render_selected_section` (divide by 1e6 for display).
"""

from __future__ import annotations

import copy
import dataclasses
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from i18n import resolve, t
from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult
from core.formatting import format_ledger_cell as _format_ledger_cell
from services.charts import (
    create_allocation_pie_chart,
    create_buyback_chart,
    create_earnings_quality_chart,
    create_ma_goodwill_chart,
    create_roic_chart,
    create_waterfall_chart,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scale_absolute_to_million(result: AuditResult) -> AuditResult:
    """When amount_unit is 'absolute', divide monetary fields by 1e6 for display.

    Mirrors :func:`ui.sections.render_selected_section` scaling, but note the
    ledger section is intentionally excluded from this scaling by the caller
    (:func:`report.builder._build_sections` passes the unscaled result to
    :func:`build_ledger_section`), matching the dashboard's
    ``section != SECTION_LEDGER`` guard. The raw audit table therefore keeps
    original absolute values regardless of amount_unit.
    """
    fields_to_scale = [
        "net_profit", "ebit", "interest_expense", "total_equity",
        "short_term_debt", "long_term_debt", "cash_and_equivalents",
        "operating_cash_flow", "capex", "da", "dividends_paid",
        "buybacks_paid", "ma_paid", "goodwill", "shares_outstanding",
        "buybacks_shares", "Market_Cap", "Owner_Earnings",
        "maintenance_capex", "total_debt", "Invested_Capital",
        "Retained_Earnings_Annual", "FCF",
    ]
    scaled_df = result.audited_df.copy()
    for f in fields_to_scale:
        if f in scaled_df.columns:
            scaled_df[f] = scaled_df[f] / 1e6

    scaled_calc = copy.copy(result.calculator)
    scaled_calc.df = scaled_calc.df.copy()
    for f in fields_to_scale:
        if f in scaled_calc.df.columns:
            scaled_calc.df[f] = scaled_calc.df[f] / 1e6

    return dataclasses.replace(result, audited_df=scaled_df, calculator=scaled_calc)


def _fmt_pct(value: float, base: float) -> str:
    if base <= 0 or pd.isna(value):
        return "N/A"
    return f"{(value / base) * 100:.1f}%"


def _fmt_ratio(value: float) -> str:
    if pd.isna(value) or np.isinf(value):
        return "N/A"
    return f"{value:.1%}"


def _fmt_num(value: float, digits: int = 2) -> str:
    if pd.isna(value):
        return "N/A"
    if np.isinf(value):
        return "∞"
    return f"{value:,.{digits}f}"


def _safe_latest(series: pd.Series) -> float:
    if series is None or series.empty:
        return np.nan
    vals = series.dropna()
    return float(vals.iloc[-1]) if not vals.empty else np.nan


def _strip_markdown(text: str) -> str:
    """Strip **bold** markers from i18n strings (PDF template uses CSS for emphasis)."""
    if not isinstance(text, str):
        return str(text)
    return text.replace("**", "")


# ---------------------------------------------------------------------------
# Section 1: Capital Allocation
# ---------------------------------------------------------------------------

def build_capital_allocation_section(
    data: CompanyAuditInput, result: AuditResult
) -> Dict[str, Any]:
    years = data.years
    start_year, end_year = min(years), max(years)
    waterfall_data = result.calculator.get_waterfall_data(start_year, end_year)
    total_ocf = waterfall_data["Total_Operating_Cash_Flow"]

    wf_fig = create_waterfall_chart(waterfall_data, start_year, end_year)
    pie_fig = create_allocation_pie_chart(waterfall_data)

    charts = [
        {"fig": wf_fig, "height": 480, "alt": "Capital allocation waterfall", "caption": None},
        {"fig": pie_fig, "height": 320, "alt": "Allocation composition", "caption": t("section.capital.composition_rate")},
    ]

    metrics = [
        {"label": t("section.capital.metric.capex_to_ocf"), "value": _fmt_pct(waterfall_data["CapEx"], total_ocf), "help": t("section.capital.metric.capex_to_ocf_help")},
        {"label": t("section.capital.metric.dividend_rate"), "value": _fmt_pct(waterfall_data["Dividends"], total_ocf), "help": t("section.capital.metric.dividend_rate_help")},
        {"label": t("section.capital.metric.buyback_rate"), "value": _fmt_pct(waterfall_data["Buybacks"], total_ocf), "help": t("section.capital.metric.buyback_rate_help")},
        {"label": t("section.capital.metric.ma_rate"), "value": _fmt_pct(waterfall_data["M_and_A"], total_ocf), "help": t("section.capital.metric.ma_rate_help")},
    ]

    return {
        "title": t("section.capital.title"),
        "intro": _strip_markdown(
            t("section.capital.desc.cumulative", start_year=start_year, end_year=end_year)
        ),
        "bullets": [],
        "charts": charts,
        "metrics_header": t("section.capital.diagnostics"),
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# Section 2: ROIC & ROIIC
# ---------------------------------------------------------------------------

def build_roic_roiic_section(params: AuditParams, result: AuditResult) -> Dict[str, Any]:
    fig = create_roic_chart(
        result.audited_df,
        result.roiic_retained_col_1,
        result.roiic_retained_col_2,
        params.roiic_window_1,
        params.roiic_window_2,
        params.roiic_retained_lag,
    )

    return {
        "title": t("section.roic.title"),
        "intro": t("section.roic.intro"),
        "bullets": [
            _strip_markdown(t("section.roic.intro.bullet1")),
            _strip_markdown(t("section.roic.intro.bullet2")),
        ],
        "charts": [{"fig": fig, "height": 480, "alt": "ROIC vs ROIIC trend", "caption": None}],
        "guidance_header": _strip_markdown(t("section.roic.guidance.header")),
        "guidance_bullets": [
            _strip_markdown(t("section.roic.guidance.bullet1")),
            _strip_markdown(t("section.roic.guidance.bullet2")),
        ],
    }


# ---------------------------------------------------------------------------
# Section 3: Buyback
# ---------------------------------------------------------------------------

def build_buyback_section(data: CompanyAuditInput, result: AuditResult) -> Dict[str, Any]:
    display_df = result.audited_df.copy()
    fx_rate = display_df["exchange_rate_to_reporting_currency"]
    display_df["Intrinsic_Value_Share_Market_Currency"] = display_df["Intrinsic_Value_Share"] / fx_rate
    display_df["Buyback_Price_Share_Market_Currency"] = display_df["Buyback_Price_Share"] / fx_rate
    display_df["dividends_paid_market_currency"] = display_df["dividends_paid"] / fx_rate
    display_df["buybacks_paid_market_currency"] = display_df["buybacks_paid"] / fx_rate

    chart_fig = create_buyback_chart(display_df, data.market_currency)

    # Detail table
    audit_df = display_df[
        ["dividends_paid_market_currency", "buybacks_paid_market_currency", "buybacks_shares",
         "Buyback_Price_Share_Market_Currency", "Intrinsic_Value_Share_Market_Currency",
         "Buyback_to_Intrinsic_Ratio", "Buyback_Audit_Rating"]
    ].copy()

    if data.amount_unit == "absolute":
        audit_df["dividends_paid_market_currency"] *= 1e6
        audit_df["buybacks_paid_market_currency"] *= 1e6
        audit_df["buybacks_shares"] *= 1e6

    col_headers = [
        t("section.buyback.col.total_dividends", currency=data.market_currency),
        t("section.buyback.col.buyback_paid", currency=data.market_currency),
        t("section.buyback.col.buyback_shares"),
        t("section.buyback.col.buyback_price", currency=data.market_currency),
        t("section.buyback.col.intrinsic_value", currency=data.market_currency),
        t("section.buyback.col.buyback_to_intrinsic"),
        t("section.buyback.col.audit_rating"),
    ]

    rows: List[List[str]] = []
    for year, row in audit_df.iterrows():
        ratio = row["Buyback_to_Intrinsic_Ratio"]
        rating = row["Buyback_Audit_Rating"]
        rows.append([
            str(year),
            f"{row['dividends_paid_market_currency']:,.0f}",
            f"{row['buybacks_paid_market_currency']:,.0f}",
            f"{row['buybacks_shares']:,.0f}",
            _fmt_num(row["Buyback_Price_Share_Market_Currency"]),
            _fmt_num(row["Intrinsic_Value_Share_Market_Currency"]),
            f"{ratio:.2%}" if not pd.isna(ratio) else "N/A",
            t(f"buyback.rating.{rating}") if isinstance(rating, str) else str(rating),
        ])

    table = {
        "caption": t("section.buyback.detail_header"),
        "headers": ["Year"] + col_headers,
        "rows": rows,
    }

    return {
        "title": t("section.buyback.title"),
        "intro": _strip_markdown(t("section.buyback.intro")),
        "bullets": [],
        "charts": [{"fig": chart_fig, "height": 480, "alt": "Buyback audit chart", "caption": None}],
        "tables": [table],
    }


# ---------------------------------------------------------------------------
# Section 4: M&A and Goodwill
# ---------------------------------------------------------------------------

def build_ma_goodwill_section(data: CompanyAuditInput, params: AuditParams, result: AuditResult) -> Dict[str, Any]:
    acq_col_1 = f"Acquisition_ROIIC_{params.roiic_window_1}Y"
    acq_col_2 = f"Acquisition_ROIIC_{params.roiic_window_2}Y"
    fig = create_ma_goodwill_chart(
        result.audited_df, acq_col_1, acq_col_2,
        params.roiic_window_1, params.roiic_window_2, params.roiic_retained_lag,
    )

    df = result.audited_df
    ma_total = float(df["ma_paid"].sum()) if "ma_paid" in df.columns else 0.0
    gw_latest = float(df["goodwill"].iloc[-1]) if "goodwill" in df.columns else 0.0
    gw_equity_latest = _safe_latest(df["Goodwill_to_Equity"]) if "Goodwill_to_Equity" in df.columns else np.nan
    acq_latest = _safe_latest(df[acq_col_2]) if acq_col_2 in df.columns else np.nan

    gw_growth_col = next((c for c in df.columns if c.startswith("Goodwill_vs_NOPAT_Growth_")), None)
    gw_growth_latest = _safe_latest(df[gw_growth_col]) if gw_growth_col else np.nan

    metrics = [
        {"label": t("section.ma.col.ma_spend"), "value": f"{data.currency} {ma_total:,.1f}M", "help": t("section.ma.col.ma_spend_help")},
        {"label": t("section.ma.col.goodwill_balance"), "value": f"{data.currency} {gw_latest:,.1f}M", "help": t("section.ma.col.goodwill_balance_help")},
        {"label": t("section.ma.col.goodwill_to_equity"), "value": _fmt_ratio(gw_equity_latest), "help": t("section.ma.col.goodwill_to_equity_help")},
        {"label": t("section.ma.col.acquisition_roiic"), "value": _fmt_ratio(acq_latest), "help": t("section.ma.col.acquisition_roiic_help")},
    ]

    alert = None
    if not pd.isna(gw_growth_latest):
        if gw_growth_latest > 0.05:
            alert = {"kind": "warning", "text": _strip_markdown(t("section.ma.warning.gw_growth", diff=gw_growth_latest))}
        elif gw_growth_latest < -0.05:
            alert = {"kind": "success", "text": _strip_markdown(t("section.ma.success.gw_growth", diff=gw_growth_latest))}

    return {
        "title": t("section.ma.title"),
        "intro": t("section.ma.intro"),
        "bullets": [
            _strip_markdown(t("section.ma.intro.bullet1")),
            _strip_markdown(t("section.ma.intro.bullet2")),
            _strip_markdown(t("section.ma.intro.bullet3")),
        ],
        "alert": alert,
        "charts": [{"fig": fig, "height": 480, "alt": "M&A and goodwill chart", "caption": None}],
        "metrics_header": t("section.capital.diagnostics"),
        "metrics": metrics,
        "guidance_header": _strip_markdown(t("section.ma.guidance.header")),
        "guidance_bullets": [
            _strip_markdown(t("section.ma.guidance.bullet1")),
            _strip_markdown(t("section.ma.guidance.bullet2")),
        ],
    }


# ---------------------------------------------------------------------------
# Section 5: Earnings Quality
# ---------------------------------------------------------------------------

def build_earnings_quality_section(data: CompanyAuditInput, result: AuditResult) -> Dict[str, Any]:
    fig = create_earnings_quality_chart(result.audited_df)

    df = result.audited_df
    recent = df.tail(5)

    oe_ratio_latest = _safe_latest(df["OE_to_NetProfit"]) if "OE_to_NetProfit" in df.columns else np.nan
    fcf_ni_latest = _safe_latest(df["FCF_to_NetIncome"]) if "FCF_to_NetIncome" in df.columns else np.nan
    accruals_latest = _safe_latest(df["Accruals_Ratio"]) if "Accruals_Ratio" in df.columns else np.nan
    oeps_latest = _safe_latest(df["OEPS"]) if "OEPS" in df.columns else np.nan

    oe_vals = recent["Owner_Earnings"].dropna() if "Owner_Earnings" in recent.columns else pd.Series(dtype=float)
    np_vals = recent["net_profit"].dropna() if "net_profit" in recent.columns else pd.Series(dtype=float)
    if not oe_vals.empty and not np_vals.empty and len(oe_vals) == len(np_vals) and (np_vals > 0).all():
        oe_cagr = (oe_vals.iloc[-1] / oe_vals.iloc[0]) ** (1 / max(len(oe_vals) - 1, 1)) - 1
    else:
        oe_cagr = np.nan

    metrics = [
        {"label": t("section.eq.metric.oe_to_np"), "value": _fmt_ratio(oe_ratio_latest), "help": t("section.eq.metric.oe_to_np_help")},
        {"label": t("section.eq.metric.fcf_to_ni"), "value": _fmt_ratio(fcf_ni_latest), "help": t("section.eq.metric.fcf_to_ni_help")},
        {"label": t("section.eq.metric.accruals_ratio"), "value": _fmt_ratio(accruals_latest), "help": t("section.eq.metric.accruals_ratio_help")},
        {"label": t("section.eq.metric.oeps"), "value": _fmt_num(oeps_latest), "help": t("section.eq.metric.oeps_help")},
    ]

    bullets = [
        _strip_markdown(t("section.eq.intro.bullet1")),
        _strip_markdown(t("section.eq.intro.bullet2")),
        _strip_markdown(t("section.eq.intro.bullet3")),
        _strip_markdown(t("section.eq.intro.bullet4")),
    ]

    summary_text = None
    if not pd.isna(oe_cagr):
        summary_text = _strip_markdown(t("section.eq.oeps_cagr", n_years=len(oe_vals), cagr=oe_cagr))

    return {
        "title": t("section.eq.title"),
        "intro": t("section.eq.intro"),
        "bullets": bullets,
        "charts": [{"fig": fig, "height": 480, "alt": "Earnings quality chart", "caption": None}],
        "metrics_header": t("section.capital.diagnostics"),
        "metrics": metrics,
        "guidance_header": _strip_markdown(t("section.eq.guidance.header")),
        "guidance_bullets": [
            _strip_markdown(t("section.eq.guidance.bullet1")),
            _strip_markdown(t("section.eq.guidance.bullet2")),
        ],
        "summary": summary_text,
    }


# ---------------------------------------------------------------------------
# Section 6: Checklist
# ---------------------------------------------------------------------------

def build_checklist_section(result: AuditResult) -> Dict[str, Any]:
    principles_data: List[Dict[str, Any]] = []
    for p in result.checklist["principles"]:
        status = p["status"]
        principles_data.append({
            "status": status,
            "badge": t(f"badge.{status}") if status in ("pass", "fail", "warning", "insufficient_data") else status,
            "principle_label": t("section.checklist.principle_n", index=p["index"]),
            "title": t(p["title_key"]),
            "actual_label": t("section.checklist.actual_value"),
            "value": resolve(p["value"]),
            "benchmark_label": t("section.checklist.benchmark"),
            "benchmark": resolve(p["benchmark"]),
            "description": resolve(p["description"]),
        })

    summary_text = _strip_markdown(
        t("section.checklist.summary_header", summary=resolve(result.checklist["summary"]))
        + t("section.checklist.disclaimer1")
        + t("section.checklist.disclaimer2")
    )

    return {
        "title": t("section.checklist.title"),
        "intro": _strip_markdown(t("section.checklist.intro")),
        "bullets": [],
        "principles": principles_data,
        "summary": summary_text,
    }


# ---------------------------------------------------------------------------
# Section 7: Ledger (full audit table)
# ---------------------------------------------------------------------------

# Column display names grouped into thematic chunks so the wide table
# stays readable across PDF pages.
_LEDGER_CHUNKS = [
    ("inputs", [
        "net_profit", "ebit", "tax_rate", "interest_expense", "total_equity",
        "short_term_debt", "long_term_debt", "cash_and_equivalents",
        "operating_cash_flow", "capex", "da", "dividends_paid",
        "buybacks_paid", "buybacks_shares", "ma_paid", "goodwill",
        "shares_outstanding", "avg_stock_price",
    ]),
    ("core", [
        "NOPAT", "Invested_Capital", "ROIC", "Owner_Earnings",
        "Market_Cap", "Retained_Earnings_Annual", "maintenance_capex", "FCF",
    ]),
    ("ratios", [
        "Goodwill_to_Equity", "Goodwill_to_IC", "MA_to_OCF",
        "OE_to_NetProfit", "FCF_to_NetIncome", "Accruals_Ratio", "OEPS",
    ]),
    ("valuation", [
        "Intrinsic_Value_Share", "Buyback_Price_Share",
        "Buyback_to_Intrinsic_Ratio", "Buyback_Audit_Rating",
    ]),
]

_LEDGER_CHUNK_LABELS = {
    "inputs": "Inputs",
    "core": "Core Metrics",
    "ratios": "Ratios",
    "valuation": "Valuation & Buyback",
}


def build_ledger_section(data: CompanyAuditInput, result: AuditResult) -> Dict[str, Any]:
    df = result.audited_df
    years = list(df.index)
    tables: List[Dict[str, Any]] = []

    # Get all numeric columns as UI does
    ui_numeric_cols = list(df.select_dtypes(include="number").columns)
    
    # Collect columns already claimed by other chunks
    claimed_by_others = set()
    for chunk_key, cols in _LEDGER_CHUNKS:
        if chunk_key != "inputs":
            claimed_by_others.update(cols)
            
    # Redefine inputs chunk to be everything in UI not in other chunks
    dynamic_inputs = [c for c in ui_numeric_cols if c not in claimed_by_others]

    for chunk_key, cols in _LEDGER_CHUNKS:
        target_cols = dynamic_inputs if chunk_key == "inputs" else cols
        present = [c for c in target_cols if c in df.columns]
        if not present:
            continue
        headers = ["Year"] + present
        rows: List[List[str]] = []
        for year in years:
            row = [str(year)]
            for col in present:
                row.append(_format_ledger_cell(df.at[year, col], col))
            rows.append(row)
        tables.append({
            "caption": _LEDGER_CHUNK_LABELS.get(chunk_key, chunk_key.title()),
            "headers": headers,
            "rows": rows,
        })

    return {
        "title": t("section.ledger.title"),
        "intro": t("section.ledger.intro"),
        "bullets": [],
        "tables": tables,
    }


# ---------------------------------------------------------------------------
# Appendix: AuditParams
# ---------------------------------------------------------------------------

def build_params_appendix(params: AuditParams) -> List[Dict[str, str]]:
    return [
        {"name": t("sidebar.params.maintenance_capex_ratio"), "value": f"{params.maintenance_capex_ratio:.2%}"},
        {"name": t("sidebar.params.roiic_window_1"), "value": f"{params.roiic_window_1}"},
        {"name": t("sidebar.params.roiic_window_2"), "value": f"{params.roiic_window_2}"},
        {"name": t("sidebar.params.roiic_retained_lag"), "value": f"{params.roiic_retained_lag}"},
        {"name": t("sidebar.params.wacc"), "value": f"{params.wacc:.2%}"},
        {"name": t("sidebar.params.growth_stage_1"), "value": f"{params.growth_stage_1:.2%}"},
        {"name": t("sidebar.params.growth_stage_2"), "value": f"{params.growth_stage_2:.2%}"},
        {"name": t("sidebar.params.terminal_growth"), "value": f"{params.terminal_growth:.2%}"},
        {"name": "Stage 1 Years", "value": f"{params.stage_1_years}"},
        {"name": "Stage 2 Years", "value": f"{params.stage_2_years}"},
    ]
