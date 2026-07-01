"""Font face CSS generation for audit reports.

Provides ``@font-face`` CSS blocks for both PDF (WeasyPrint, local file paths)
and HTML (browser, base64-inlined) report paths.

Two font families are provided:

* **Sans** (IBM Plex Sans + IBM Plex Sans TC) — used by the dashboard
  (``app.py``, ``hkex_app/theme.py``). Latin fonts are base64-inlined for
  the dashboard; CJK uses system TC font fallback.
* **Serif** (IBM Plex Serif + Noto Serif TC) — used by the report (PDF/HTML).
  Latin fonts are embedded (local files for PDF, base64 for HTML); CJK uses
  local files for PDF (WeasyPrint subsets) and system fallback for HTML.

Font files live in ``assets/fonts/`` and are licensed under the SIL Open Font
License 1.1 (see ``assets/fonts/LICENSE.txt``).
"""

from __future__ import annotations

import base64
import os
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FONTS_DIR = _PROJECT_ROOT / "assets" / "fonts"

FONT_FAMILY_STACK = (
    "'IBM Plex Sans', 'IBM Plex Sans TC', "
    "'PingFang TC', 'Microsoft JhengHei', 'Noto Sans CJK TC', sans-serif"
)

SERIF_FONT_FAMILY_STACK = (
    "'IBM Plex Serif', 'Noto Serif CJK TC', serif"
)

_LATIN_FONTS = [
    ("IBM Plex Sans", 400, "normal", "IBMPlexSans-Regular.ttf"),
    ("IBM Plex Sans", 500, "normal", "IBMPlexSans-Medium.ttf"),
    ("IBM Plex Sans", 600, "normal", "IBMPlexSans-SemiBold.ttf"),
    ("IBM Plex Sans", 700, "normal", "IBMPlexSans-Bold.ttf"),
]

_SERIF_LATIN_FONTS = [
    ("IBM Plex Serif", 400, "normal", "IBMPlexSerif-Regular.otf", "opentype"),
    ("IBM Plex Serif", 500, "normal", "IBMPlexSerif-Medium.otf", "opentype"),
    ("IBM Plex Serif", 600, "normal", "IBMPlexSerif-SemiBold.otf", "opentype"),
    ("IBM Plex Serif", 700, "normal", "IBMPlexSerif-Bold.otf", "opentype"),
]

_SERIF_CJK_FONTS = [
    ("Noto Serif CJK TC", 400, "normal", "NotoSerifTC-Regular.otf", "opentype"),
    ("Noto Serif CJK TC", 500, "normal", "NotoSerifTC-Medium.otf", "opentype"),
    ("Noto Serif CJK TC", 700, "normal", "NotoSerifTC-Bold.otf", "opentype"),
]


@lru_cache(maxsize=1)
def get_pdf_font_face_css() -> str:
    """Return ``@font-face`` CSS with local file paths for WeasyPrint.

    WeasyPrint resolves relative URLs via ``base_url="."`` (set in
    :func:`services.report.builder.build_report`), reading font files
    directly from disk and subsetting them into the PDF.
    """
    rules = []
    for family, weight, style, filename in _LATIN_FONTS:
        rel_path = f"assets/fonts/{filename}"
        rules.append(
            f'@font-face {{\n'
            f'  font-family: "{family}";\n'
            f'  font-weight: {weight};\n'
            f'  font-style: {style};\n'
            f'  src: url("{rel_path}") format("truetype");\n'
            f'}}'
        )
    return "\n".join(rules)


@lru_cache(maxsize=1)
def get_html_font_face_css() -> str:
    """Return ``@font-face`` CSS with base64-inlined Latin fonts for HTML.

    Keeps the HTML report self-contained (offline-capable). Only Latin
    weights are inlined (~1 MB base64); CJK relies on system TC fonts
    (PingFang TC on macOS, Microsoft JhengHei on Windows, Noto Sans CJK TC
    on Linux) to avoid a ~13 MB payload.
    """
    rules = []
    for family, weight, style, filename in _LATIN_FONTS:
        font_path = _FONTS_DIR / filename
        if not font_path.exists():
            continue
        data = font_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        rules.append(
            f'@font-face {{\n'
            f'  font-family: "{family}";\n'
            f'  font-weight: {weight};\n'
            f'  font-style: {style};\n'
            f'  src: url(data:font/truetype;base64,{b64}) format("truetype");\n'
            f'}}'
        )
    return "\n".join(rules)


@lru_cache(maxsize=1)
def get_pdf_serif_font_face_css() -> str:
    """Return serif ``@font-face`` CSS with local file paths for WeasyPrint.

    Embeds both Latin (IBM Plex Serif, 4 weights) and CJK (Noto Serif TC,
    3 weights) via local OTF files. WeasyPrint embeds CFF/OTF fonts as
    CIDFontType0 with FontFile3; TrueType (TTF) fonts are NOT embedded by
    WeasyPrint, so OTF format is required for cross-platform PDF fidelity.
    """
    rules = []
    for family, weight, style, filename, fmt in _SERIF_LATIN_FONTS + _SERIF_CJK_FONTS:
        rel_path = f"assets/fonts/{filename}"
        rules.append(
            f'@font-face {{\n'
            f'  font-family: "{family}";\n'
            f'  font-weight: {weight};\n'
            f'  font-style: {style};\n'
            f'  src: url("{rel_path}") format("{fmt}");\n'
            f'}}'
        )
    return "\n".join(rules)


@lru_cache(maxsize=1)
def get_html_serif_font_face_css() -> str:
    """Return serif ``@font-face`` CSS with base64-inlined Latin fonts for HTML.

    Only Latin (IBM Plex Serif, 4 weights, ~1 MB base64) is inlined to keep
    the HTML self-contained without bloating (~24 MB for CJK). CJK relies
    on system serif TC fonts (Songti TC on macOS, PMingLiU on Windows,
    Noto Serif CJK TC on Linux).
    """
    rules = []
    for family, weight, style, filename, fmt in _SERIF_LATIN_FONTS:
        font_path = _FONTS_DIR / filename
        if not font_path.exists():
            continue
        data = font_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        rules.append(
            f'@font-face {{\n'
            f'  font-family: "{family}";\n'
            f'  font-weight: {weight};\n'
            f'  font-style: {style};\n'
            f'  src: url(data:font/opentype;base64,{b64}) format("{fmt}");\n'
            f'}}'
        )
    return "\n".join(rules)
