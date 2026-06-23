import streamlit as st

from services.audit_pipeline import run_audit
from ui.sections import render_navigation, render_selected_section, render_summary
from ui.sidebar import render_sidebar


def configure_page() -> None:
    st.set_page_config(
        page_title="管理层资本配置效率审计系统",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="📈",
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

            .main {
                background-color: #0f111a;
                color: #ffffff;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.25rem;
                font-weight: 700;
                line-height: 1.5rem !important;
                height: 1.8rem !important;
                display: flex;
                align-items: center;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.9rem;
                color: #8892b0;
                line-height: 1.2rem !important;
                height: 1.4rem !important;
                display: flex;
                align-items: center;
            }
            h1, h2, h3 {
                font-weight: 700 !important;
            }
            .badge-A {
                background-color: #00ffcc;
                color: #0f111a;
                padding: 0.3rem 0.6rem;
                border-radius: 0.3rem;
                font-weight: bold;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    configure_page()
    st.markdown("## 📈 管理层资本配置效率审计系统")

    data, params = render_sidebar()
    try:
        result = run_audit(data, params)
    except Exception as exc:
        st.error(f"❌ 审计模型运行失败：{exc}")
        st.stop()

    render_summary(data, result.checklist)
    selected_section = render_navigation()
    render_selected_section(selected_section, data, params, result)


if __name__ == "__main__":
    main()
