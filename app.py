import streamlit as st

from i18n import t
from services.audit_pipeline import run_audit
from ui.sections import render_navigation, render_selected_section, render_summary
from ui.sidebar import render_sidebar, render_pdf_export_button


def configure_page() -> None:
    st.set_page_config(
        page_title=t("app.title"),
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon=None,
    )
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400;1,700&family=Noto+Sans+SC:wght@100..900&display=swap');

            /* Global styling for Courier Prime */
            html, body, [data-testid="stAppViewContainer"], .main, .sidebar {
                font-family: 'Courier Prime', 'Noto Sans SC', monospace;
            }

            /* Apply Courier Prime to standard text and UI widgets */
            h1, h2, h3, h4, h5, h6, p, label, .stMetric, .stMarkdown, input, select, textarea {
                font-family: 'Courier Prime', 'Noto Sans SC', monospace !important;
            }

            button {
                font-family: 'Courier Prime', 'Noto Sans SC', monospace;
            }

            /* Exempt icons from global font styling to ensure stSidebar collapse double arrow displays properly */
            [data-testid="stIcon"], [class*="Icon"], [class*="icon"], [class*="stIcon"] {
                font-family: inherit !important;
            }
            
            /* Remove shadows, card rounding and enforce 1px flat borders */
            div[data-testid="stMetric"] {
                border-radius: 0px !important;
                border: 1px solid rgba(128, 128, 128, 0.2) !important;
                background-color: transparent !important;
                padding: 1rem !important;
                box-shadow: none !important;
            }
            
            div[data-testid="stForm"] {
                border-radius: 0px !important;
                border: 1px solid rgba(128, 128, 128, 0.2) !important;
                box-shadow: none !important;
                background-color: transparent !important;
            }

            button, select, input, textarea {
                border-radius: 0px !important;
                box-shadow: none !important;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.25rem;
                font-weight: 700;
                line-height: 1.5rem !important;
                height: 1.8rem !important;
                display: flex;
                align-items: center;
                color: inherit !important;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.9rem;
                color: inherit !important;
                opacity: 0.6;
                line-height: 1.2rem !important;
                height: 1.4rem !important;
                display: flex;
                align-items: center;
            }
            h1, h2, h3 {
                font-weight: 700 !important;
            }
            .badge-A {
                background-color: transparent;
                color: inherit;
                padding: 0.2rem 0.5rem;
                border-radius: 0px !important;
                border: 1px solid rgba(128, 128, 128, 0.5);
                font-weight: bold;
            }
            
            /* Shimo Docs Style Alerts / Callouts */
            div[data-testid="stAlert"] {
                background-color: rgba(128, 128, 128, 0.04) !important;
                border: 1px solid rgba(128, 128, 128, 0.1) !important;
                border-left: 4px solid rgba(128, 128, 128, 0.6) !important;
                border-radius: 0px !important;
                color: inherit !important;
                box-shadow: none !important;
                padding: 0.8rem 1rem !important;
            }
            div[data-testid="stAlert"] > div {
                background-color: transparent !important;
                color: inherit !important;
            }
            div[data-testid="stAlert"] p, div[data-testid="stAlert"] span, div[data-testid="stAlert"] div {
                color: inherit !important;
            }
            div[data-testid="stAlert"] svg {
                fill: currentColor !important;
                color: inherit !important;
            }

            /* Sharp straight-angle borders for selectboxes, text areas, dataframes, and nested elements */
            div[data-testid="stSelectbox"],
            div[data-testid="stSelectbox"] *,
            div[data-testid="stTextArea"],
            div[data-testid="stTextArea"] *,
            div[data-testid="stDataFrame"],
            div[data-testid="stDataFrame"] *,
            div[data-testid="stTable"],
            div[data-testid="stTable"] *,
            div[data-testid="stTextInput"],
            div[data-testid="stTextInput"] *,
            div[data-testid="stNumberInput"],
            div[data-testid="stNumberInput"] *,
            div[data-testid="stCheckbox"],
            div[data-testid="stCheckbox"] *,
            div[data-baseweb="select"],
            div[data-baseweb="select"] *,
            div[data-baseweb="textarea"],
            div[data-baseweb="textarea"] *,
            div[data-baseweb="input"],
            div[data-baseweb="input"] *,
            textarea,
            select {
                border-radius: 0px !important;
            }

            /* Old-money navigation caption: small uppercase tracked label */
            .nav-caption {
                font-size: 0.7rem !important;
                letter-spacing: 0.25em !important;
                text-transform: uppercase !important;
                opacity: 0.55;
                margin: 0 0 0.35rem 0 !important;
                font-family: 'Courier Prime', 'Noto Sans SC', monospace;
            }

            /* Top navigation selectbox: compact, hairline border, transparent ground */
            div[data-testid="stSelectbox"] {
                max-width: 360px;
            }
            div[data-testid="stSelectbox"] > div > div {
                background-color: transparent !important;
                border: 1px solid rgba(128, 128, 128, 0.3) !important;
                box-shadow: none !important;
            }
            div[data-testid="stSelectbox"] [data-testid="stSelectboxArrowIcon"] svg {
                color: rgba(128, 128, 128, 0.6) !important;
            }

            /* Dropdown popover menu: flat, hairline, monospace, muted hover */
            div[data-baseweb="popover"] ul[role="listbox"] {
                border-radius: 0px !important;
                border: 1px solid rgba(128, 128, 128, 0.3) !important;
                background-color: var(--background-color, #ffffff) !important;
                box-shadow: none !important;
                font-family: 'Courier Prime', 'Noto Sans SC', monospace !important;
            }
            div[data-baseweb="popover"] ul[role="listbox"] li {
                border-radius: 0px !important;
            }
            div[data-baseweb="popover"] ul[role="listbox"] li:hover,
            div[data-baseweb="popover"] ul[role="listbox"] li[aria-selected="true"] {
                background-color: rgba(128, 128, 128, 0.08) !important;
                color: inherit !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    configure_page()

    data, params = render_sidebar()
    try:
        result = run_audit(data, params)
    except Exception as exc:
        st.error(f"❌ 审计模型运行失败：{exc}")
        st.stop()

    render_pdf_export_button(data, params, result)

    col_nav, col_spacer = st.columns([1, 2])
    with col_nav:
        selected_section = render_navigation()

    render_summary(data, result.checklist)
    render_selected_section(selected_section, data, params, result)


if __name__ == "__main__":
    main()
