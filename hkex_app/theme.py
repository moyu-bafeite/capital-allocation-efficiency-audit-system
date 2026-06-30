"""Page configuration and self-contained CSS.

Font stack is consistent with the audit ``app.py`` (Courier Prime +
Noto Sans SC, loaded from Google Fonts). Layout/sizing styles (flat
borders, removed shadows) are kept lightweight and independent.
"""
import os

import streamlit as st

from hkex_app.i18n import t

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
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400;1,700&family=Noto+Sans+SC:wght@100..900&display=swap');

            /* Global styling for Courier Prime (matches app.py) */
            html, body, [data-testid="stAppViewContainer"], .main, .sidebar {
                font-family: 'Courier Prime', 'Noto Sans SC', monospace;
            }

            /* Apply Courier Prime to standard text and UI widgets */
            h1, h2, h3, h4, h5, h6, p, label, li, .stMetric, .stMarkdown, input, select, textarea, div[role="listbox"], ul[role="listbox"], li[role="option"], div[data-baseweb="popover"], div[data-baseweb="select"], div[data-baseweb="select"] span {
                font-family: 'Courier Prime', 'Noto Sans SC', monospace !important;
            }

            button {
                font-family: 'Courier Prime', 'Noto Sans SC', monospace;
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
