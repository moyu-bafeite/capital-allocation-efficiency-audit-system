"""Render Plotly figures for both PDF (static PNG) and HTML (interactive) reports.

Two rendering paths share the same ``go.Figure`` objects produced by
``ui.charts``:

* **PDF path** — ``fig_to_base64_png`` rasterizes via kaleido for WeasyPrint.
  Kept for archival/printable output; requires system libs (cairo/pango).
* **HTML path** — ``fig_to_plotly_div`` embeds the live Plotly div so the
  report reader can hover/zoom/legend-toggle. Zero system dependencies;
  Plotly.js is inlined once in ``<head>`` for offline use (~4.6 MB).
"""

from __future__ import annotations

import base64
import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator, Optional

import plotly.graph_objects as go

logger = logging.getLogger(__name__)

_PDF_FONT_FAMILY = "Courier Prime, Courier New, monospace"


def _has_right_axis_title(fig: go.Figure) -> bool:
    """Check if the figure has a right-side yaxis2 with a non-empty title."""
    yaxis2 = getattr(fig.layout, "yaxis2", None) if fig.layout else None
    if yaxis2 is None:
        return False
    title = getattr(yaxis2, "title", None)
    if title is None:
        return False
    text = title if isinstance(title, str) else getattr(title, "text", None)
    return bool(text and str(text).strip())


def _right_margin(fig: go.Figure, default: int = 25) -> int:
    """Return right margin: wider when a right y-axis title is present."""
    return 80 if _has_right_axis_title(fig) else default


@contextmanager
def kaleido_server() -> Iterator[None]:
    """Keep a single kaleido Chromium instance alive for the duration of the block.

    Falls back gracefully if the sync server API is unavailable (older kaleido);
    in that case each ``to_image`` call spawns its own subprocess.
    """
    started = False
    try:
        import kaleido
        kaleido.start_sync_server(silence_warnings=True)
        started = True
        logger.debug("kaleido sync server started")
    except Exception as exc:
        logger.debug("kaleido sync server unavailable, falling back to per-call spawn: %s", exc)
    try:
        yield
    finally:
        if started:
            try:
                import kaleido
                kaleido.stop_sync_server()
                logger.debug("kaleido sync server stopped")
            except Exception as exc:
                logger.debug("kaleido sync server stop failed: %s", exc)


def _apply_pdf_layout(fig: go.Figure, height: int = 480) -> go.Figure:
    """Mutate and return ``fig`` with print-friendly layout defaults."""
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=_PDF_FONT_FAMILY, size=12, color="#1a1a1a"),
        margin=dict(l=55, r=_right_margin(fig), t=55, b=80),
        height=height,
        title=dict(font=dict(size=14)),
        legend=dict(font=dict(size=10)),
        xaxis=dict(
            gridcolor="rgba(128,128,128,0.15)",
            zerolinecolor="rgba(128,128,128,0.3)",
            tickangle=-30,
            automargin=True,
        ),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.3)"),
    )
    return fig


def fig_to_base64_png(fig: go.Figure, scale: int = 2, height: int = 480) -> str:
    """Convert a Plotly figure to a base64-encoded PNG data URI (PDF path)."""
    _apply_pdf_layout(fig, height=height)
    png_bytes = fig.to_image(format="png", scale=scale)
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def safe_fig_to_base64_png(fig: go.Figure, scale: int = 2, height: int = 480) -> Optional[str]:
    """Same as :func:`fig_to_base64_png` but returns ``None`` on failure."""
    try:
        return fig_to_base64_png(fig, scale=scale, height=height)
    except Exception as exc:
        logger.warning("Chart rendering failed; section will degrade to text only: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Interactive HTML path
# ---------------------------------------------------------------------------

_PLOTLY_DIV_CONFIG = {
    "displayModeBar": True,
    "responsive": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["sendDataToCloud"],
}


@lru_cache(maxsize=1)
def get_plotlyjs_inline() -> str:
    """Return the full Plotly.js library source as a <script>-ready string.

    Cached so repeated report builds don't re-fetch the ~4.6 MB blob.
    Inlined once in ``<head>`` to make the HTML report fully offline-capable.
    """
    from plotly.offline import get_plotlyjs

    return get_plotlyjs()


def fig_to_plotly_div(fig: go.Figure, height: int = 480) -> str:
    """Convert a Plotly figure to a self-contained interactive <div> block.

    The div does NOT include the Plotly.js library — that must be injected
    once in ``<head>`` via :func:`get_plotlyjs_inline`. Each div is ~7 KB.

    Args:
        fig: Plotly figure (layout will be re-skinned for screen viewing).
        height: Chart height in pixels.

    Returns:
        HTML string containing ``<div>`` + ``<script>`` (Plotly.newPlot call).
    """
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=_PDF_FONT_FAMILY, size=13, color="#1a1a1a"),
        margin=dict(l=55, r=_right_margin(fig), t=55, b=80),
        height=height,
        title=dict(font=dict(size=15)),
        legend=dict(font=dict(size=11)),
        xaxis=dict(
            gridcolor="rgba(128,128,128,0.15)",
            zerolinecolor="rgba(128,128,128,0.3)",
            tickangle=-30,
            automargin=True,
        ),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.3)"),
    )
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config=_PLOTLY_DIV_CONFIG,
    )


def safe_fig_to_plotly_div(fig: go.Figure, height: int = 480) -> Optional[str]:
    """Same as :func:`fig_to_plotly_div` but returns ``None`` on failure."""
    try:
        return fig_to_plotly_div(fig, height=height)
    except Exception as exc:
        logger.warning("Interactive chart rendering failed; degrading to text: %s", exc)
        return None

