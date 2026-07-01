import json
from typing import Tuple
import streamlit as st
from i18n import t, get_lang, set_lang, LANGUAGES, LANGUAGE_LABELS
from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult
from datalayer.manager import DataManager

def get_empty_template() -> str:
    template = {
        "ticker": "XXXX.HK",
        "company_name": t("sidebar.template.company_name"),
        "currency": "HKD",
        "amount_unit": "absolute",
        "market_currency": "HKD",
        "exchange_rate_to_reporting_currency": [1.0, 1.0, 1.0, 1.0, 1.0],
        "closing_exchange_rate_to_reporting_currency": [1.0, 1.0, 1.0, 1.0, 1.0],
        "years": [2020, 2021, 2022, 2023, 2024],
        "financials": {
            "net_profit": [100.0, 120.0, 150.0, 130.0, 180.0],
            "ebit": [120.0, 140.0, 180.0, 150.0, 210.0],
            "revenue": [500.0, 550.0, 600.0, 580.0, 650.0],
            "tax_rate": [0.165, 0.165, 0.165, 0.165, 0.165],
            "interest_expense": [5.0, 6.0, 7.0, 8.0, 9.0],
            "total_equity": [800.0, 900.0, 1000.0, 1050.0, 1200.0],
            "short_term_debt": [50.0, 60.0, 70.0, 80.0, 70.0],
            "long_term_debt": [150.0, 180.0, 200.0, 220.0, 210.0],
            "cash_and_equivalents": [200.0, 250.0, 300.0, 280.0, 350.0],
            "accounts_receivable": [80.0, 90.0, 100.0, 95.0, 110.0],
            "inventory": [60.0, 70.0, 80.0, 75.0, 85.0],
            "accounts_payable": [70.0, 80.0, 90.0, 85.0, 100.0],
            "operating_cash_flow": [130.0, 150.0, 190.0, 160.0, 220.0],
            "operating_income_before_wc_change": [110.0, 130.0, 170.0, 140.0, 200.0],
            "cash_from_business_operations": [130.0, 150.0, 190.0, 160.0, 220.0],
            "capex": [60.0, 70.0, 80.0, 65.0, 75.0],
            "da": [40.0, 45.0, 50.0, 55.0, 60.0],
            "dividends_paid": [30.0, 40.0, 50.0, 50.0, 60.0],
            "buybacks_paid": [0.0, 0.0, 10.0, 15.0, 30.0],
            "buybacks_shares": [0.0, 0.0, 2000000.0, 3500000.0, 6000000.0],
            "ma_paid": [10.0, 20.0, 0.0, 30.0, 15.0],
            "goodwill": [100.0, 115.0, 115.0, 140.0, 150.0],
            "cashflow_impairment_adjustment": [0.0, 0.0, 0.0, 0.0, 0.0],
            "cashflow_fair_value_adjustment": [0.0, 0.0, 0.0, 0.0, 0.0],
            "income_impairment_charges": [0.0, 0.0, 0.0, 0.0, 0.0],
            "income_fair_value_changes": [0.0, 0.0, 0.0, 0.0, 0.0],
            "shares_outstanding": [100000000.0, 100000000.0, 98000000.0, 94500000.0, 88500000.0],
            "avg_stock_price": [10.0, 12.0, 9.0, 8.0, 11.0],
            "closing_stock_price": [10.5, 11.0, 8.5, 9.0, 12.0],
        },
    }
    return json.dumps(template, indent=2, ensure_ascii=False)

def _render_toolbox() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sidebar.toolbox"))
    st.sidebar.download_button(
        label=t("sidebar.download_template"),
        data=get_empty_template(),
        file_name="capital_allocation_template.json",
        mime="application/json",
    )

def render_report_export_button(
    data: CompanyAuditInput, params: AuditParams, result: AuditResult
) -> None:
    """Render a sidebar section that exports the full audit as a report.

    Provides a format selector (PDF / HTML) and a single "Generate" button.
    Should be called after :func:`render_sidebar` and after ``run_audit`` has
    produced ``result``. The generated file is cached in session state keyed
    by ticker + format so it survives Streamlit re-runs without rebuilding.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sidebar.report_export_header"))

    fmt = st.sidebar.radio(
        t("sidebar.report_format.label"),
        options=["html", "pdf"],
        format_func=lambda f: t(f"sidebar.report_format.{f}"),
        index=0,
        help=t("sidebar.report_format.help"),
    )

    button_key = "build_report_btn"
    if st.sidebar.button(t("sidebar.report_export_button"), key=button_key):
        from services.report import build_report, build_report_html

        try:
            with st.spinner(t("sidebar.report_export_building")):
                if fmt == "pdf":
                    payload = build_report(data, params, result)
                else:
                    payload = build_report_html(data, params, result)
            st.session_state["report_bytes"] = payload
            st.session_state["report_format"] = fmt
            st.session_state["report_ticker"] = data.ticker
        except ImportError as exc:
            st.sidebar.error(t("sidebar.report_export_dep_error", exc=exc))
        except Exception as exc:
            st.sidebar.error(t("sidebar.report_export_error", exc=exc))

    payload = st.session_state.get("report_bytes")
    cached_fmt = st.session_state.get("report_format")
    cached_ticker = st.session_state.get("report_ticker")
    if payload and cached_ticker == data.ticker and cached_fmt == fmt:
        if fmt == "pdf":
            st.sidebar.download_button(
                label=t("sidebar.report_download"),
                data=payload,
                file_name=f"capital_allocation_audit_{data.ticker}.pdf",
                mime="application/pdf",
            )
        else:
            st.sidebar.download_button(
                label=t("sidebar.report_download"),
                data=payload,
                file_name=f"capital_allocation_audit_{data.ticker}.html",
                mime="text/html",
            )

def _render_params(data: CompanyAuditInput) -> AuditParams:
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sidebar.params_header"))

    st.sidebar.markdown(f"#### {t('sidebar.params.section1')}")
    maintenance_capex_ratio = st.sidebar.slider(
        t("sidebar.params.maintenance_capex_ratio"),
        min_value=0.10,
        max_value=1.00,
        value=0.50,
        step=0.05,
        help=t("sidebar.params.maintenance_capex_help"),
    )

    st.sidebar.markdown(f"#### {t('sidebar.params.section2')}")
    num_years = len(data.years)
    max_roiic_window = max(1, num_years - 1)
    roiic_window_1 = int(
        st.sidebar.number_input(
            t("sidebar.params.roiic_window_1"),
            min_value=1,
            max_value=max_roiic_window,
            value=min(3, max_roiic_window),
            step=1,
            help=t("sidebar.params.roiic_window_1_help"),
        )
    )
    roiic_window_2 = int(
        st.sidebar.number_input(
            t("sidebar.params.roiic_window_2"),
            min_value=1,
            max_value=max_roiic_window,
            value=min(5, max_roiic_window),
            step=1,
            help=t("sidebar.params.roiic_window_2_help"),
        )
    )
    max_roiic_retained_lag = max(0, num_years - max(roiic_window_1, roiic_window_2))
    roiic_retained_lag = int(
        st.sidebar.number_input(
            t("sidebar.params.roiic_retained_lag"),
            min_value=0,
            max_value=max_roiic_retained_lag,
            value=min(1, max_roiic_retained_lag),
            step=1,
            help=t("sidebar.params.roiic_retained_lag_help"),
        )
    )

    st.sidebar.markdown(f"#### {t('sidebar.params.section3')}")
    wacc = st.sidebar.slider(
        t("sidebar.params.wacc"),
        min_value=0.05,
        max_value=0.50,
        value=0.08,
        step=0.005,
        format="%.3f",
    )
    growth_stage_1 = st.sidebar.slider(
        t("sidebar.params.growth_stage_1"),
        min_value=-0.10,
        max_value=0.30,
        value=0.08,
        step=0.01,
        format="%.2f",
    )
    growth_stage_2 = st.sidebar.slider(
        t("sidebar.params.growth_stage_2"),
        min_value=-0.10,
        max_value=0.20,
        value=0.04,
        step=0.01,
        format="%.2f",
    )
    terminal_growth = st.sidebar.slider(
        t("sidebar.params.terminal_growth"),
        min_value=-0.05,
        max_value=0.05,
        value=0.02,
        step=0.01,
        format="%.2f",
    )

    if wacc <= terminal_growth:
        st.sidebar.error(t("sidebar.error.wacc_le_terminal"))
        st.stop()

    return AuditParams(
        maintenance_capex_ratio=maintenance_capex_ratio,
        roiic_window_1=roiic_window_1,
        roiic_window_2=roiic_window_2,
        roiic_retained_lag=roiic_retained_lag,
        wacc=wacc,
        growth_stage_1=growth_stage_1,
        growth_stage_2=growth_stage_2,
        terminal_growth=terminal_growth,
    )

DATA_SOURCE_OPTIONS = {
    "futu": "sidebar.data_source.futu",
    "upload": "sidebar.data_source.upload",
}

def render_sidebar() -> Tuple[CompanyAuditInput, AuditParams]:
    lang = st.sidebar.selectbox(
        t("sidebar.language"),
        LANGUAGES,
        format_func=lambda l: LANGUAGE_LABELS[l],
        index=LANGUAGES.index(get_lang())
    )
    if lang != get_lang():
        set_lang(lang)

    st.sidebar.subheader(t("sidebar.data_source_header"))
    data_source_opt = st.sidebar.selectbox(
        t("sidebar.data_source.label"),
        ["futu", "upload"],
        format_func=lambda k: t(DATA_SOURCE_OPTIONS[k]),
    )

    data_obj = None

    if data_source_opt == "upload":
        uploaded_file = st.sidebar.file_uploader(t("sidebar.upload.label"), type=["json"])
        if uploaded_file is not None:
            try:
                raw_data = json.load(uploaded_file)
                data_obj = CompanyAuditInput(**raw_data)
                st.sidebar.success(t("sidebar.upload.success"))
            except Exception as exc:
                st.sidebar.error(t("sidebar.upload.parse_error", exc=exc))
                st.stop()
        else:
            st.info(t("sidebar.upload.prompt"))
            st.stop()

    else:
        provider_name = "futu"
        default_ticker = "HK.00388"

        with st.sidebar.form("api_fetch_form"):
            ticker_input = st.text_input(t("sidebar.futu.ticker_input"), value=default_ticker, help=t("sidebar.futu.ticker_help")).strip()

            years_range = st.slider(
                t("sidebar.futu.year_range"),
                min_value=2010,
                max_value=2025,
                value=(2016, 2025),
                step=1
            )
            years_list = list(range(years_range[0], years_range[1] + 1))

            force_refresh = st.checkbox(t("sidebar.futu.force_refresh"), value=False)
            fetch_btn = st.form_submit_button(t("sidebar.futu.fetch_btn"))

        source_key = f"{ticker_input}_{provider_name}_{years_range[0]}_{years_range[1]}"

        bypass_cache = force_refresh and fetch_btn

        if not bypass_cache and "cached_input_data" in st.session_state and st.session_state.get("cached_source_key") == source_key:
            data_obj = st.session_state["cached_input_data"]
        else:
            manager = DataManager()
            if fetch_btn:
                try:
                    with st.spinner(t("sidebar.futu.loading")):
                        data_obj = manager.get_audit_input(
                            ticker=ticker_input,
                            provider_name=provider_name,
                            years=years_list,
                            refresh=force_refresh
                        )
                    st.session_state["cached_input_data"] = data_obj
                    st.session_state["cached_source_key"] = source_key
                    st.sidebar.success(t("sidebar.futu.load_success", ticker=ticker_input, year_start=years_range[0], year_end=years_range[1]))
                except Exception as exc:
                    st.sidebar.error(t("sidebar.futu.load_error", exc=exc))
                    st.stop()
            else:
                cached_dict = None
                if not bypass_cache:
                    cached_dict = manager.cache.get_audit_input(ticker_input, provider_name)

                if cached_dict and set(years_list).issubset(set(cached_dict.get("years", []))):
                    try:
                        sliced_dict = manager._slice_cached_dict(cached_dict, years_list)
                        data_obj = CompanyAuditInput(**sliced_dict)
                        st.session_state["cached_input_data"] = data_obj
                        st.session_state["cached_source_key"] = source_key
                    except Exception:
                        pass

                if data_obj is None:
                    st.info(t("sidebar.futu.start_prompt"))
                    st.stop()

    _render_toolbox()
    params = _render_params(data_obj)
    return data_obj, params
