"""
Render Plotly figures into static images for PDF embedding.

The UI layer keeps figures transparent so they adapt to Streamlit's theme;
for PDF export we re-skin them onto a white canvas with a monospace font
that matches the app's "old-money" Courier Prime aesthetic.

Performance: kaleido v1 spins up a Chromium subprocess per ``to_image`` call
(~15s each). Wrap batch rendering in :func:`kaleido_server` to keep one
Chromium instance alive across all charts (cuts 6-chart render from ~90s
to ~5s).
"""

from __future__ import annotations

import base64
import logging
from contextlib import contextmanager
from typing import Iterator, Optional

import plotly.graph_objects as go

logger = logging.getLogger(__name__)

_PDF_FONT_FAMILY = "Courier Prime, Courier New, monospace"


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
        margin=dict(l=55, r=25, t=55, b=45),
        height=height,
        title=dict(font=dict(size=14)),
        legend=dict(font=dict(size=10)),
        xaxis=dict(gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.3)"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.3)"),
    )
    return fig


def fig_to_base64_png(fig: go.Figure, scale: int = 2, height: int = 480) -> str:
    """Convert a Plotly figure to a base64-encoded PNG data URI.

    Args:
        fig: Plotly figure (will be re-skinned onto white background).
        scale: Pixel scale factor (2 = retina-quality).
        height: Figure height in pixels before scaling.

    Returns:
        ``data:image/png;base64,...`` string suitable for ``<img src="">``.
    """
    _apply_pdf_layout(fig, height=height)
    png_bytes = fig.to_image(format="png", scale=scale)
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def safe_fig_to_base64_png(fig: go.Figure, scale: int = 2, height: int = 480) -> Optional[str]:
    """Same as :func:`fig_to_base64_png` but returns ``None`` on failure.

    Used so a single broken chart degrades gracefully instead of failing
    the entire PDF build.
    """
    try:
        return fig_to_base64_png(fig, scale=scale, height=height)
    except Exception as exc:
        logger.warning("Chart rendering failed; section will degrade to text only: %s", exc)
        return None
