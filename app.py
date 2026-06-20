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
            .main {
                background-color: #0f111a;
                color: #ffffff;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.25rem;
                font-weight: 700;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.9rem;
                color: #8892b0;
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

    render_summary(data, result.scorecard)
    selected_section = render_navigation()
    render_selected_section(selected_section, data, params, result)


if __name__ == "__main__":
    main()
