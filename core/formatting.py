"""Shared ledger cell formatting helpers.

Single source of truth for "ratio/price vs amount" column classification so
the Streamlit dashboard (``ui.sections.render_ledger_section``) and the
PDF/HTML report (``report.sections._format_ledger_cell``) render the audit
table identically.

Classification rule (applied to the column name):

1. Substring keywords (case-insensitive): ``rate``, ``ratio``, ``price``,
   ``roic``, ``roiic``, ``rule``, ``value``, ``percent``.
2. Explicit whitelist for ratio/per-share columns whose names don't contain
   any of the keywords above: ``Goodwill_to_Equity``, ``Goodwill_to_IC``,
   ``MA_to_OCF``, ``OE_to_NetProfit``, ``FCF_to_NetIncome``, ``OEPS``.
3. Dynamic prefix ``Goodwill_vs_NOPAT_Growth_`` (window-suffixed columns).

Any other numeric column is treated as an amount/share count and formatted
with 0 decimals.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

_KEYWORDS = ("rate", "ratio", "price", "roic", "roiic", "rule", "value", "percent")

_EXPLICIT_RATIO_COLUMNS = frozenset(
    {
        "Goodwill_to_Equity",
        "Goodwill_to_IC",
        "MA_to_OCF",
        "OE_to_NetProfit",
        "FCF_to_NetIncome",
        "OEPS",
    }
)

_RATIO_PREFIXES = ("Goodwill_vs_NOPAT_Growth_",)


def is_ratio_or_price_column(col: str) -> bool:
    """Return True if ``col`` should be rendered with 2-decimal precision."""
    if not isinstance(col, str):
        return False
    lower = col.lower()
    if any(kw in lower for kw in _KEYWORDS):
        return True
    if col in _EXPLICIT_RATIO_COLUMNS:
        return True
    if any(col.startswith(prefix) for prefix in _RATIO_PREFIXES):
        return True
    return False


def format_ledger_cell(value: Any, col: str) -> str:
    """Format a single audit-table cell for display.

    - Strings are returned unchanged (e.g. ``Buyback_Audit_Rating`` values).
    - NaN/NA → ``"—"``.
    - ±inf → ``"∞"``.
    - Ratio/price columns → ``f"{value:,.2f}"``.
    - Amount/share columns → ``f"{value:,.0f}"``.
    """
    if isinstance(value, str):
        return value
    if pd.isna(value):
        return "—"
    if np.isinf(value):
        return "∞"
    try:
        if is_ratio_or_price_column(col):
            return f"{value:,.2f}"
        return f"{value:,.0f}"
    except (ValueError, TypeError):
        return str(value)
