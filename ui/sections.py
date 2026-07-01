import streamlit as st
import numpy as np
import pandas as pd

from core.formatting import is_ratio_or_price_column
from i18n import t, resolve
from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult
from services.charts import (
    create_allocation_pie_chart,
    create_buyback_chart,
    create_earnings_quality_chart,
    create_ma_goodwill_chart,
    create_roic_chart,
    create_waterfall_chart,
)


SECTION_CAPITAL_ALLOCATION = "capital_allocation"
SECTION_ROIC_ROIIC = "roic_roiic"
SECTION_BUYBACK = "buyback"
SECTION_MA_GOODWILL = "ma_goodwill"
SECTION_EARNINGS_QUALITY = "earnings_quality"
SECTION_CHECKLIST = "checklist"
SECTION_LEDGER = "ledger"
SECTIONS = [
    SECTION_CAPITAL_ALLOCATION,
    SECTION_ROIC_ROIIC,
    SECTION_BUYBACK,
    SECTION_MA_GOODWILL,
    SECTION_EARNINGS_QUALITY,
    SECTION_CHECKLIST,
    SECTION_LEDGER,
]

SECTION_KEY_MAP = {
    SECTION_CAPITAL_ALLOCATION: "section.nav.capital_allocation",
    SECTION_ROIC_ROIIC: "section.nav.roic_roiic",
    SECTION_BUYBACK: "section.nav.buyback",
    SECTION_MA_GOODWILL: "section.nav.ma_goodwill",
    SECTION_EARNINGS_QUALITY: "section.nav.earnings_quality",
    SECTION_CHECKLIST: "section.nav.checklist",
    SECTION_LEDGER: "section.nav.ledger",
}


def format_compact_currency(value: float, currency: str, amount_unit: str) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    absolute = value * 1e6 if amount_unit == "million" else value
    abs_val = abs(absolute)
    if abs_val >= 1e9:
        return f"{currency} {absolute / 1e9:.1f}B"
    if abs_val >= 1e6:
        return f"{currency} {absolute / 1e6:.1f}M"
    return f"{currency} {absolute:,.0f}"


def render_summary(data: CompanyAuditInput, checklist: dict) -> None:
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.metric(t("metric.label.company"), f"{data.company_name} / {data.ticker}")
    with col_meta2:
        st.metric(t("metric.label.years"), f"{data.years[0]}-{data.years[-1]} ({len(data.years)})")
    with col_meta3:
        display_unit = t("metric.unit.absolute") if data.amount_unit == "absolute" else data.amount_unit
        st.metric(t("metric.label.currency_unit"), f"{data.currency} / {display_unit}")
    with col_meta4:
        st.metric(t("metric.label.market_currency"), f"{data.market_currency}")
    st.markdown("---")


def render_navigation() -> str:
    st.markdown(
        f'<p class="nav-caption">{t("app.nav_caption")}</p>',
        unsafe_allow_html=True,
    )
    return st.selectbox(
        t("section.nav.label"),
        SECTIONS,
        format_func=lambda s: t(SECTION_KEY_MAP.get(s, s)),
        label_visibility="collapsed",
    )


def render_capital_allocation_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown(f"#### {t('section.capital.title')}")

    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        time_mode = st.radio(
            t("section.capital.time_mode.label"),
            ["cumulative", "single_year"],
            format_func=lambda k: t(f"section.capital.time_mode.{k}"),
            index=0,
        )

    years = data.years
    start_year = min(years)
    end_year = max(years)
    with col_sel2:
        if time_mode == "cumulative":
            selected_years = st.slider(
                t("section.capital.year_range"),
                min_value=int(start_year),
                max_value=int(end_year),
                value=(int(start_year), int(end_year)),
                step=1,
            )
            start_year_selected = selected_years[0]
            end_year_selected = selected_years[1]
            n_years = end_year_selected - start_year_selected + 1
            st.info(t("section.capital.current_range", start_year=start_year_selected, end_year=end_year_selected, n_years=n_years))
        else:
            selected_year = st.selectbox(t("section.capital.single_year.label"), years, index=len(years) - 1)
            start_year_selected = selected_year
            end_year_selected = selected_year
            st.info(t("section.capital.current_single_year", year=selected_year))

    if start_year_selected == end_year_selected:
        st.markdown(t("section.capital.desc.single_year", year=start_year_selected))
    else:
        st.markdown(t("section.capital.desc.cumulative", start_year=start_year_selected, end_year=end_year_selected))

    waterfall_data = result.calculator.get_waterfall_data(start_year_selected, end_year_selected)
    st.plotly_chart(create_waterfall_chart(waterfall_data, start_year_selected, end_year_selected), use_container_width=True)
    st.markdown(f"###### {t('section.capital.composition_rate')}")
    st.plotly_chart(create_allocation_pie_chart(waterfall_data, data.currency), use_container_width=True)

    st.markdown(f"###### {t('section.capital.diagnostics')}")
    c1, c2, c3, c4 = st.columns(4)
    total_ocf = waterfall_data["Total_Operating_Cash_Flow"]

    def _pct(value: float, base: float) -> str:
        return f"{(value / base) * 100:.1f}%" if base > 0 else "N/A"

    with c1:
        st.metric(t("section.capital.metric.capex_to_ocf"), _pct(waterfall_data['CapEx'], total_ocf), help=t("section.capital.metric.capex_to_ocf_help"))
    with c2:
        st.metric(t("section.capital.metric.dividend_rate"), _pct(waterfall_data['Dividends'], total_ocf), help=t("section.capital.metric.dividend_rate_help"))
    with c3:
        st.metric(t("section.capital.metric.buyback_rate"), _pct(waterfall_data['Buybacks'], total_ocf), help=t("section.capital.metric.buyback_rate_help"))
    with c4:
        st.metric(t("section.capital.metric.ma_rate"), _pct(waterfall_data['M_and_A'], total_ocf), help=t("section.capital.metric.ma_rate_help"))


def render_roic_roiic_section(params: AuditParams, result: AuditResult) -> None:
    st.markdown(f"#### {t('section.roic.title')}")
    st.markdown(t("section.roic.intro"))
    st.markdown(t("section.roic.intro.bullet1"))
    st.markdown(t("section.roic.intro.bullet2"))
    st.plotly_chart(
        create_roic_chart(
            result.audited_df,
            result.roiic_retained_col_1,
            result.roiic_retained_col_2,
            params.roiic_window_1,
            params.roiic_window_2,
            params.roiic_retained_lag,
        ),
        use_container_width=True,
    )
    st.markdown(f"{t('section.roic.guidance.header')}")
    st.markdown(f"{t('section.roic.guidance.bullet1')}")
    st.markdown(f"{t('section.roic.guidance.bullet2')}")


def render_buyback_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown(f"#### {t('section.buyback.title')}")
    st.markdown(t("section.buyback.intro"))

    display_df = result.audited_df.copy()
    fx_rate = display_df["exchange_rate_to_reporting_currency"]
    display_df["Intrinsic_Value_Share_Market_Currency"] = display_df["Intrinsic_Value_Share"] / fx_rate
    display_df["Buyback_Price_Share_Market_Currency"] = display_df["Buyback_Price_Share"] / fx_rate
    display_df["dividends_paid_market_currency"] = display_df["dividends_paid"] / fx_rate
    display_df["buybacks_paid_market_currency"] = display_df["buybacks_paid"] / fx_rate

    st.plotly_chart(create_buyback_chart(display_df, data.market_currency), use_container_width=True)

    st.markdown(f"###### {t('section.buyback.detail_header')}")
    audit_display_df = display_df[
        [
            "dividends_paid_market_currency",
            "buybacks_paid_market_currency",
            "buybacks_shares",
            "Buyback_Price_Share_Market_Currency",
            "Intrinsic_Value_Share_Market_Currency",
            "Buyback_to_Intrinsic_Ratio",
            "Buyback_Audit_Rating",
        ]
    ].copy()

    if data.amount_unit == "absolute":
        audit_display_df["dividends_paid_market_currency"] *= 1e6
        audit_display_df["buybacks_paid_market_currency"] *= 1e6

    col_total_div = t("section.buyback.col.total_dividends", currency=data.market_currency)
    col_buyback_paid = t("section.buyback.col.buyback_paid", currency=data.market_currency)
    col_buyback_shares = t("section.buyback.col.buyback_shares")
    col_buyback_price = t("section.buyback.col.buyback_price", currency=data.market_currency)
    col_intrinsic = t("section.buyback.col.intrinsic_value", currency=data.market_currency)
    col_ratio = t("section.buyback.col.buyback_to_intrinsic")
    col_rating = t("section.buyback.col.audit_rating")

    audit_display_df.columns = [
        col_total_div,
        col_buyback_paid,
        col_buyback_shares,
        col_buyback_price,
        col_intrinsic,
        col_ratio,
        col_rating,
    ]

    st.dataframe(
        audit_display_df.style.format(
            {
                col_total_div: "{:,.0f}",
                col_buyback_paid: "{:,.0f}",
                col_buyback_shares: "{:,.0f}",
                col_buyback_price: "{:,.2f}",
                col_intrinsic: "{:,.2f}",
                col_ratio: "{:.2%}",
                col_rating: lambda k: t(f"buyback.rating.{k}") if isinstance(k, str) else str(k),
            }
        ).map(
            lambda k: "font-weight: bold; text-decoration: underline; text-underline-offset: 3px;"
            if isinstance(k, str) and k == "excellent"
            else "font-style: italic; font-weight: bold; border-bottom: 2px double rgba(128,128,128,0.8);"
            if isinstance(k, str) and k == "blind"
            else "opacity: 0.5; font-style: italic;"
            if isinstance(k, str) and k == "none"
            else "",
            subset=[col_rating],
        ),
        use_container_width=True,
    )


def render_ma_goodwill_section(data: CompanyAuditInput, params: AuditParams, result: AuditResult) -> None:
    st.markdown(f"#### {t('section.ma.title')}")
    st.markdown(t("section.ma.intro"))
    st.markdown(t("section.ma.intro.bullet1"))
    st.markdown(t("section.ma.intro.bullet2"))
    st.markdown(t("section.ma.intro.bullet3"))

    acq_col_1 = f"Acquisition_ROIIC_{params.roiic_window_1}Y"
    acq_col_2 = f"Acquisition_ROIIC_{params.roiic_window_2}Y"
    st.plotly_chart(
        create_ma_goodwill_chart(
            result.audited_df,
            acq_col_1,
            acq_col_2,
            params.roiic_window_1,
            params.roiic_window_2,
            params.roiic_retained_lag,
        ),
        use_container_width=True,
    )

    display_df = result.audited_df
    goodwill_growth_col = next(
        (c for c in display_df.columns if c.startswith("Goodwill_vs_NOPAT_Growth_")),
        None,
    )

    ma_total = float(display_df["ma_paid"].sum()) if "ma_paid" in display_df.columns else 0.0
    gw_latest = float(display_df["goodwill"].iloc[-1]) if "goodwill" in display_df.columns else 0.0
    gw_equity_latest = float(display_df["Goodwill_to_Equity"].dropna().iloc[-1]) if "Goodwill_to_Equity" in display_df.columns and not display_df["Goodwill_to_Equity"].dropna().empty else np.nan
    acq_latest = float(display_df[acq_col_2].dropna().iloc[-1]) if acq_col_2 in display_df.columns and not display_df[acq_col_2].dropna().empty else np.nan
    gw_growth_latest = float(display_df[goodwill_growth_col].dropna().iloc[-1]) if goodwill_growth_col and not display_df[goodwill_growth_col].dropna().empty else np.nan

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("section.ma.col.ma_spend"), f"{data.currency} {ma_total: .1f}M", help=t("section.ma.col.ma_spend_help"))
    with c2:
        st.metric(t("section.ma.col.goodwill_balance"), f"{data.currency} {gw_latest:,.1f}M", help=t("section.ma.col.goodwill_balance_help"))
    with c3:
        st.metric(t("section.ma.col.goodwill_to_equity"), f"{gw_equity_latest:.1%}" if not pd.isna(gw_equity_latest) else "N/A", help=t("section.ma.col.goodwill_to_equity_help"))
    with c4:
        st.metric(t("section.ma.col.acquisition_roiic"), f"{acq_latest:.1%}" if not pd.isna(acq_latest) else "N/A", help=t("section.ma.col.acquisition_roiic_help"))

    if not pd.isna(gw_growth_latest):
        if gw_growth_latest > 0.05:
            st.warning(t("section.ma.warning.gw_growth", diff=gw_growth_latest))
        elif gw_growth_latest < -0.05:
            st.success(t("section.ma.success.gw_growth", diff=gw_growth_latest))

    st.markdown(f"{t('section.ma.guidance.header')}")
    st.markdown(f"{t('section.ma.guidance.bullet1')}")
    st.markdown(f"{t('section.ma.guidance.bullet2')}")


def render_earnings_quality_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown(f"#### {t('section.eq.title')}")
    st.markdown(t("section.eq.intro"))
    st.markdown(t("section.eq.intro.bullet1"))
    st.markdown(t("section.eq.intro.bullet2"))
    st.markdown(t("section.eq.intro.bullet3"))
    st.markdown(t("section.eq.intro.bullet4"))

    st.plotly_chart(
        create_earnings_quality_chart(result.audited_df),
        use_container_width=True,
    )

    display_df = result.audited_df
    recent = display_df.tail(5)

    def _safe_latest(col):
        if col not in display_df.columns:
            return np.nan
        vals = display_df[col].dropna()
        return float(vals.iloc[-1]) if not vals.empty else np.nan

    oe_ratio_latest = _safe_latest("OE_to_NetProfit")
    fcf_ni_latest = _safe_latest("FCF_to_NetIncome")
    accruals_latest = _safe_latest("Accruals_Ratio")
    oeps_latest = _safe_latest("OEPS")

    oe_vals = recent["Owner_Earnings"].dropna() if "Owner_Earnings" in recent.columns else pd.Series(dtype=float)
    np_vals = recent["net_profit"].dropna() if "net_profit" in recent.columns else pd.Series(dtype=float)
    if not oe_vals.empty and not np_vals.empty and len(oe_vals) == len(np_vals) and (np_vals > 0).all():
        oe_cagr = (oe_vals.iloc[-1] / oe_vals.iloc[0]) ** (1 / max(len(oe_vals) - 1, 1)) - 1
    else:
        oe_cagr = np.nan

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("section.eq.metric.oe_to_np"), f"{oe_ratio_latest:.1%}" if not pd.isna(oe_ratio_latest) else "N/A", help=t("section.eq.metric.oe_to_np_help"))
    with c2:
        st.metric(t("section.eq.metric.fcf_to_ni"), f"{fcf_ni_latest:.1%}" if not pd.isna(fcf_ni_latest) else "N/A", help=t("section.eq.metric.fcf_to_ni_help"))
    with c3:
        st.metric(t("section.eq.metric.accruals_ratio"), f"{accruals_latest:.1%}" if not pd.isna(accruals_latest) else "N/A", help=t("section.eq.metric.accruals_ratio_help"))
    with c4:
        st.metric(t("section.eq.metric.oeps"), f"{oeps_latest:,.2f}" if not pd.isna(oeps_latest) else "N/A", help=t("section.eq.metric.oeps_help"))

    if not pd.isna(oe_cagr):
        st.info(t("section.eq.oeps_cagr", n_years=len(oe_vals), cagr=oe_cagr))

    st.markdown(f"**{t('section.eq.guidance.header')}**\n")
    st.markdown(f"{t('section.eq.guidance.bullet1')}\n")
    st.markdown(f"{t('section.eq.guidance.bullet2')}\n")


def render_checklist_section(result: AuditResult) -> None:
    st.markdown(f"#### {t('section.checklist.title')}")
    st.markdown(t("section.checklist.intro"))

    checklist = result.checklist
    principles = checklist["principles"]

    status_config = {
        "pass": {"icon": t("badge.pass"), "style": "font-weight: 700; color: #4ca66b;"},
        "fail": {"icon": t("badge.fail"), "style": "font-weight: 700; color: #c0463e; text-decoration: underline;"},
        "warning": {"icon": t("badge.warning"), "style": "font-weight: 700; color: #b8860b; border-bottom: 1px dashed rgba(128,128,128,0.6); display: inline-block;"},
        "insufficient_data": {"icon": t("badge.insufficient_data"), "style": "font-weight: 400; color: #8a8a8a; opacity: 0.6;"},
    }

    for p in principles:
        cfg = status_config.get(p["status"], status_config["insufficient_data"])
        st.markdown(
            f"""
            <div style="background-color: transparent; padding: 1.2rem 0rem; border-radius: 0px; border-bottom: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 0.5rem;">
                <p style="font-size: 1.05rem; margin: 0 0 0.5rem 0; {cfg['style']}">
                    {cfg['icon']} | {t('section.checklist.principle_n', index=p['index'])}：{t(p['title_key'])}
                </p>
                <p style="font-size: 0.95rem; margin: 0.25rem 0;">
                    <span style="opacity: 0.6;">{t('section.checklist.actual_value')}</span><strong>{resolve(p['value'])}</strong>
                    &nbsp;&nbsp;
                    <span style="opacity: 0.6;">{t('section.checklist.benchmark')}</span><strong>{resolve(p['benchmark'])}</strong>
                </p>
                <p style="font-size: 0.9rem; opacity: 0.8; margin: 0.5rem 0 0 0;">{resolve(p['description'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.info(
        t("section.checklist.summary_header", summary=resolve(checklist['summary']))
        + t("section.checklist.disclaimer1")
        + t("section.checklist.disclaimer2")
    )


def render_ledger_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown(f"#### {t('section.ledger.title')}")
    st.markdown(t("section.ledger.intro"))
    numeric_columns = result.audited_df.select_dtypes(include="number").columns

    formatters = {}
    for column in numeric_columns:
        if is_ratio_or_price_column(column):
            formatters[column] = "{:,.2f}"
        else:
            formatters[column] = "{:,.0f}"

    st.dataframe(result.audited_df.style.format(formatters), use_container_width=True)
    st.download_button(
        label=t("section.ledger.export_csv"),
        data=result.audited_df.to_csv().encode("utf-8-sig"),
        file_name=f"capital_allocation_audit_{data.ticker}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown(f"#### {t('section.ledger.duckdb_title')}")
    st.markdown(t("section.ledger.duckdb_intro"))

    try:
        import duckdb
        from datalayer.cache import DATABASE_URL
        import os

        SQL_TEMPLATES = {
            "latest_financials": "SELECT * FROM raw_financials ORDER BY fetched_at DESC LIMIT 10;",
            "exchange_rates": "SELECT * FROM exchange_rates ORDER BY fetched_at DESC;",
            "stock_prices": "SELECT * FROM stock_prices ORDER BY fetched_at DESC;",
            "audit_inputs": "SELECT ticker, provider, fetched_at FROM audit_inputs ORDER BY fetched_at DESC;",
            "custom": "",
        }

        if os.path.exists(DATABASE_URL):
            col_sql1, col_sql2 = st.columns([1, 3])
            with col_sql1:
                sql_key = st.selectbox(
                    t("section.ledger.sql_template.label"),
                    list(SQL_TEMPLATES.keys()),
                    format_func=lambda k: t(f"section.ledger.sql_template.{k}"),
                )

            sql_query = SQL_TEMPLATES.get(sql_key, "")
            with col_sql2:
                custom_sql = st.text_area(
                    t("section.ledger.sql.editor_label"),
                    value=sql_query,
                    height=100,
                    placeholder=t("section.ledger.sql.placeholder"),
                )

            if custom_sql.strip():
                try:
                    with duckdb.connect(DATABASE_URL, read_only=True) as conn:
                        df_res = conn.execute(custom_sql).df()
                    st.success(t("section.ledger.sql.success"))
                    st.dataframe(df_res, use_container_width=True)
                except Exception as query_exc:
                    st.error(t("section.ledger.sql.error", exc=query_exc))
        else:
            st.info(t("section.ledger.sql.no_cache"))
    except Exception as exc:
        st.error(t("section.ledger.sql.init_error", exc=exc))


def render_selected_section(section: str, data: CompanyAuditInput, params: AuditParams, result: AuditResult) -> None:
    if data.amount_unit == "absolute" and section != SECTION_LEDGER:
        import dataclasses
        import copy

        scaled_df = result.audited_df.copy()
        fields_to_scale = [
            "net_profit", "ebit", "interest_expense", "total_equity",
            "short_term_debt", "long_term_debt", "cash_and_equivalents",
            "operating_cash_flow", "capex", "da", "dividends_paid",
            "buybacks_paid", "ma_paid", "goodwill",
            "Market_Cap", "Owner_Earnings",
            "maintenance_capex", "total_debt", "Invested_Capital",
            "Retained_Earnings_Annual", "FCF"
        ]
        for f in fields_to_scale:
            if f in scaled_df.columns:
                scaled_df[f] = scaled_df[f] / 1e6

        scaled_calc = copy.copy(result.calculator)
        scaled_calc.df = scaled_calc.df.copy()
        for f in fields_to_scale:
            if f in scaled_calc.df.columns:
                scaled_calc.df[f] = scaled_calc.df[f] / 1e6

        result = dataclasses.replace(result, audited_df=scaled_df, calculator=scaled_calc)

    if section == SECTION_CAPITAL_ALLOCATION:
        render_capital_allocation_section(data, result)
    elif section == SECTION_ROIC_ROIIC:
        render_roic_roiic_section(params, result)
    elif section == SECTION_BUYBACK:
        render_buyback_section(data, result)
    elif section == SECTION_MA_GOODWILL:
        render_ma_goodwill_section(data, params, result)
    elif section == SECTION_EARNINGS_QUALITY:
        render_earnings_quality_section(data, result)
    elif section == SECTION_CHECKLIST:
        render_checklist_section(result)
    elif section == SECTION_LEDGER:
        render_ledger_section(data, result)
