"""Page configuration and self-contained CSS.

Font stack is consistent with the audit ``app.py`` (IBM Plex Sans +
IBM Plex Sans TC, locally embedded). Layout/sizing styles (flat
borders, removed shadows) are kept lightweight and independent.
"""
import os

import streamlit as st

from hkex_app.i18n import t
from services.report.fonts import get_html_font_face_css

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, ".cache", "audit.db")


def resolve_db_path(custom: str = "") -> str:
    """Resolve the DuckDB path: explicit arg > DATABASE_URL env > project default."""
    if custom:
        return custom
    return os.environ.get("DATABASE_URL") or _DEFAULT_DB_PATH


def configure_page() -> None:
    st.set_page_config(
        page_title=t("hkex.app.title"),
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon=None,
    )
    st.markdown(
        f"""
        <style>
            {get_html_font_face_css()}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
            /* Global styling for IBM Plex Sans (matches app.py) */
            html, body, [data-testid="stAppViewContainer"], .main, .sidebar {
                font-family: 'IBM Plex Sans', 'IBM Plex Sans TC', 'PingFang TC', 'Microsoft JhengHei', 'Noto Sans CJK TC', sans-serif;
            }

            /* Apply IBM Plex Sans to standard text and UI widgets */
            h1, h2, h3, h4, h5, h6, p, label, li, .stMetric, .stMarkdown, input, select, textarea, div[role="listbox"], ul[role="listbox"], li[role="option"], div[data-baseweb="popover"], div[data-baseweb="select"], div[data-baseweb="select"] span {
                font-family: 'IBM Plex Sans', 'IBM Plex Sans TC', 'PingFang TC', 'Microsoft JhengHei', 'Noto Sans CJK TC', sans-serif !important;
            }

            button {
                font-family: 'IBM Plex Sans', 'IBM Plex Sans TC', 'PingFang TC', 'Microsoft JhengHei', 'Noto Sans CJK TC', sans-serif;
            }

            /* Exempt icons from global font styling to ensure stSidebar collapse double arrow displays properly */
            [data-testid="stIcon"], [class*="Icon"], [class*="icon"], [class*="stIcon"] {
                font-family: inherit !important;
            }

            /* Flatten Streamlit defaults: remove rounded corners and shadows
               for a compact, data-tool feel. */
            button, select, input, textarea,
            div[data-testid="stSelectbox"],
            div[data-testid="stSelectbox"] *,
            div[data-testid="stTextInput"],
            div[data-testid="stTextInput"] *,
            div[data-testid="stNumberInput"],
            div[data-testid="stNumberInput"] *,
            div[data-testid="stDateInput"],
            div[data-testid="stDateInput"] *,
            div[data-testid="stDataFrame"],
            div[data-testid="stDataFrame"] *,
            div[data-testid="stMetric"],
            div[data-baseweb="select"],
            div[data-baseweb="select"] *,
            div[data-baseweb="input"],
            div[data-baseweb="input"] * {
                border-radius: 0px !important;
            }
            div[data-testid="stMetric"] {
                border: 1px solid rgba(128, 128, 128, 0.25) !important;
                background-color: transparent !important;
                padding: 0.75rem !important;
                box-shadow: none !important;
            }
            div[data-testid="stAlert"] {
                border-radius: 0px !important;
                box-shadow: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
