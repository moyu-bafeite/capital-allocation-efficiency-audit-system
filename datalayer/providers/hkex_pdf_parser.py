"""HKEX 月报表 PDF 解析模块（纯解析，无网络）.

从一份已下载的 HKEX 月报表 PDF bytes 中解析出已发行股本变动数据。
与抓取层 (`hkex_share_capital.py`) 解耦：本模块不发起任何 HTTP 请求，
输入是 PDF bytes，输出是结构化记录 dict 或 None。

支持两种表单格式：

  - **FF301 新版** (v1.0.0+，2021-07 报告期起)：
    Section II 标题 "II. Movements in Issued Shares"，单列已发行股数，
    报告期格式 "DD MonthName YYYY"（如 ``31 July 2021``）。
    出现在 page 1（第 2 页）。

  - **March 2019 旧版** (2021-07 报告期之前)：
    Section II 标题 "II. Movements in Issued Share Capital"，4 列布局
    （ordinary / preference / other / 备注），数字在 PDF 提取后常跨行
    （换行位置可能在 "of/the" 或 "the/month" 之间）。
    报告期格式 "DD/MM/YYYY"（HKEX 约定日在前，如 ``31/12/2020`` = 12月31日）。
    出现在 page 2（第 3 页）。

两个版本均不含 treasury 列（库存股概念在 FF301 中未保留），故
``shares_treasury = 0``，``shares_issued_excl_treasury = shares_total_issued``。

公开接口:
    from datalayer.providers.hkex_pdf_parser import parse_share_capital_pdf
    record = parse_share_capital_pdf(pdf_bytes, "00700", "Tencent", url)
"""
import logging
import re
from datetime import date
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from pypdf import PdfReader

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 共享辅助
# ----------------------------------------------------------------------
_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    # short forms seen in some extracted texts
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_month_ended(period_str: str) -> Optional[date]:
    """Parse a monthly-return report period string into a date.

    Supports three formats:
      - "DD MonthName YYYY"     (FF301 新版, e.g. "31 July 2021")
      - "MonthName DD, YYYY"    (备用, e.g. "July 31, 2021")
      - "DD/MM/YYYY"            (旧版 March 2019, e.g. "31/12/2020" = Dec 31)

    Returns None if the string cannot be parsed.
    """
    if not period_str:
        return None
    s = period_str.strip()
    # Try "DD MonthName YYYY"
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m:
        day, month_name, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        month = _MONTH_NAMES.get(month_name)
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                return None
    # Try "MonthName DD, YYYY"
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m:
        month_name, day, year = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        month = _MONTH_NAMES.get(month_name)
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                return None
    # Try "DD/MM/YYYY" (旧版 March 2019 表单, 日在前). pypdf sometimes injects
    # spaces between the day/month/year and the slashes (e.g. "31 /10/2019"),
    # so tolerate optional whitespace around each slash.
    m = re.match(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})", s)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def _extract_pub_date_from_url(pdf_url: str) -> Optional[date]:
    """Extract the publication date from a HKEX PDF URL.

    HKEX convention: /listedco/listconews/sehk/YYYY/MMDD/<filename>.pdf
    where YYYY-MMDD is the publication date.
    """
    m = re.search(r"/(\d{4})(\d{4})\d{3,}\.pdf$", pdf_url)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2)[:2])
    day = int(m.group(2)[2:])
    try:
        return date(year, month, day)
    except ValueError:
        return None


# ----------------------------------------------------------------------
# 版本检测
# ----------------------------------------------------------------------
_FORMAT_FF301 = "ff301"
_FORMAT_LEGACY = "legacy"


def _detect_format(page0_text: str) -> str:
    """Detect the PDF form version from page 0 text.

    Returns ``_FORMAT_FF301`` or ``_FORMAT_LEGACY``.

    FF301 新版 page 0 含 "FF301" 表单标识，或报告期行紧跟 "Status"。
    旧版 (March 2019) page 0 含 "Monthly Return of Equity Issuer on
    Movements in Securities" 且报告期是 DD/MM/YYYY 数字格式（无 "Status"）。
    """
    if "FF301" in page0_text:
        return _FORMAT_FF301
    # FF301 新版的报告期行: "For the month ended: 31 July 2021 Status: ..."
    if re.search(r"For the month ended:\s*[^\n]+\s+Status", page0_text):
        return _FORMAT_FF301
    # 旧版报告期: "For the month ended\n(dd/mm/yyyy) :  31/12/2020"
    if re.search(r"For the month ended[^:]*:\s*\d{1,2}/\d{1,2}/\d{4}", page0_text):
        return _FORMAT_LEGACY
    # 兜底：含旧版标题则判旧版
    if "Monthly Return of Equity Issuer on Movements in Securities" in page0_text:
        return _FORMAT_LEGACY
    # 默认按新版处理（更常见）
    return _FORMAT_FF301


# ----------------------------------------------------------------------
# 报告期解析（按版本）
# ----------------------------------------------------------------------
def _parse_report_period_ff301(page0_text: str) -> Optional[date]:
    """FF301 新版: 'For the month ended: 31 July 2021 Status: New'."""
    m = re.search(r"For the month ended:\s*([^\n]+?)\s+Status", page0_text)
    if not m:
        return None
    return _parse_month_ended(m.group(1).strip())


def _parse_report_period_legacy(page0_text: str) -> Optional[date]:
    """旧版 March 2019: 'For the month ended\\n(dd/mm/yyyy) :  31/12/2020'.

    HKEX 旧版约定 DD/MM/YYYY（日在前）。正则容忍标签与日期之间的换行、
    空格及 "(dd/mm/yyyy)" 提示文字。pypdf 有时在日期的日/月/年与斜杠之间
    注入空格（如 "31 /10/2019"），故捕获组也容忍斜杠两侧的空格。
    """
    m = re.search(
        r"For the month ended[^:]*:\s*(\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4})",
        page0_text,
    )
    if not m:
        return None
    return _parse_month_ended(m.group(1).strip())


# ----------------------------------------------------------------------
# Section II 定位（跨版本）
# ----------------------------------------------------------------------
def _find_section_ii_page(reader: PdfReader) -> Optional[int]:
    """Scan all pages and return the index of the page containing Section II.

    Matches both FF301 "II. Movements in Issued Shares" and legacy
    "II. Movements in Issued Share Capital" via the common prefix
    "II. Movements in Issued Share". Returns the first matching page index,
    or None if not found.
    """
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if re.search(r"II\.\s+Movements in Issued Share", text):
            return i
    return None


# ----------------------------------------------------------------------
# Section II 解析（按版本）
# ----------------------------------------------------------------------
def _isolate_section_ii_block(section_text: str) -> str:
    """Isolate the Section II text span to avoid false matches from Section I.

    The page that contains Section II may also carry the tail of Section I
    ("Movements in Authorised Share Capital"), whose empty "Balance at close
    of the month" rows (no number) cause the multiline Section II regex to
    run past them and grab an unrelated number (e.g. the "3" of "3. Other
    Classes of Shares"). Restricting to the span between the "II. Movements
    in Issued Share" heading and the next "III." heading eliminates this.

    If the heading is not found (defensive — caller already located the page),
    the original text is returned unchanged so behavior stays back-compatible.
    """
    i = section_text.find("II. Movements in Issued Share")
    if i < 0:
        return section_text
    j = section_text.find("III.", i + 5)
    return section_text[i:j] if j > i else section_text[i:i + 1500]


def _parse_section_ii_ff301(section_text: str) -> Tuple[Optional[int], int, Optional[int]]:
    """FF301 新版 Section II: 单列已发行股数（不跨行）。

    'Balance at close of the month 9,431,783,365' → (total, 0, total).

    保留 3 列正则作前向兼容（若遇到带 treasury 列的变体，3 列优先更精确）。
    Returns (issued_excl_treasury, treasury, total_issued) or (None, 0, None).
    """
    block = _isolate_section_ii_block(section_text)
    # 3-column variant (issued excl treasury, treasury, total) — forward compat.
    matches_3 = re.findall(
        r"Balance at close of the month\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)",
        block,
    )
    if matches_3:
        a, b, c = matches_3[0]
        return int(a.replace(",", "")), int(b.replace(",", "")), int(c.replace(",", ""))

    # 1-column variant (FF301 v1.0.x: single total-issued column).
    matches_1 = re.findall(
        r"Balance at close of the month\s+([\d,]+)",
        block,
    )
    if matches_1:
        total = int(matches_1[0].replace(",", ""))
        return total, 0, total

    return None, 0, None


def _parse_section_ii_legacy(section_text: str) -> Tuple[Optional[int], int, Optional[int]]:
    """旧版 March 2019 Section II: 4 列布局，数字跨行。

    'Balance at close of\\nthe month 9,593,912,711  N/A  N/A  N/A'
    或 'Balance at close of the\\nmonth  9,373,218,730  N/A  N/A  N/A'

    取 ordinary shares 列（第一个数字）。多行正则 `\\s+` 容忍换行位置
    在 of/the 或 the/month 之间（两种变体均已实测）。

    IMPORTANT: the Section II page of legacy PDFs also contains the tail of
    Section I, whose empty "Balance at close of the month" rows (no number)
    would let the multiline `\\s+` run past them and grab an unrelated number
    (e.g. the "3" of "3. Other Classes of Shares"). We isolate the II→III
    span first to prevent this.
    Returns (ordinary, 0, ordinary) or (None, 0, None).
    """
    block = _isolate_section_ii_block(section_text)
    # 多行正则：容忍 "of\nthe month" 和 "the\nmonth" 两种换行变体。
    matches = re.findall(
        r"Balance at close of\s+the\s+month\s+([\d,]+)",
        block,
    )
    if matches:
        ordinary = int(matches[0].replace(",", ""))
        return ordinary, 0, ordinary

    # 兜底：单行 1-col（万一某些旧版提取后未跨行）。
    matches_1 = re.findall(
        r"Balance at close of the month\s+([\d,]+)",
        block,
    )
    if matches_1:
        total = int(matches_1[0].replace(",", ""))
        return total, 0, total

    return None, 0, None


# ----------------------------------------------------------------------
# 公开入口
# ----------------------------------------------------------------------
def parse_share_capital_pdf(
    pdf_bytes: bytes,
    stock_code: str,
    company_name: str,
    pdf_url: str,
) -> Optional[Dict[str, object]]:
    """Parse a single HKEX monthly-return PDF into a share-capital record.

    Auto-detects the form version (FF301 新版 / March 2019 旧版) and routes
    to the corresponding parser. The Section II page is located by scanning
    all pages (its position differs between versions).

    :param pdf_bytes: Raw PDF file content.
    :param stock_code: Normalized 5-digit stock code (e.g. "00700").
    :param company_name: Issuer name (from stockId lookup).
    :param pdf_url: Source URL (used for pub_date extraction & audit trail).
    :return: Record dict with keys stock_code, company_name,
        report_period_date, report_year, report_month, pub_date,
        shares_issued_excl_treasury, shares_treasury, shares_total_issued,
        source_pdf_url; or None if parsing fails.
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    if len(reader.pages) < 2:
        logger.warning("PDF has fewer than 2 pages, skipping: %s", pdf_url)
        return None

    page0_text = reader.pages[0].extract_text() or ""
    fmt = _detect_format(page0_text)
    logger.debug("Detected PDF format '%s' for %s", fmt, pdf_url)

    # Report period
    if fmt == _FORMAT_FF301:
        report_period_date = _parse_report_period_ff301(page0_text)
    else:
        report_period_date = _parse_report_period_legacy(page0_text)
    if report_period_date is None:
        logger.warning(
            "Could not parse report period (format=%s) from %s", fmt, pdf_url,
        )
        return None

    # Section II page (position differs between versions)
    sec_idx = _find_section_ii_page(reader)
    if sec_idx is None:
        logger.warning("Could not locate Section II page in %s", pdf_url)
        return None
    section_text = reader.pages[sec_idx].extract_text() or ""

    if fmt == _FORMAT_FF301:
        issued, treasury, total_issued = _parse_section_ii_ff301(section_text)
    else:
        issued, treasury, total_issued = _parse_section_ii_legacy(section_text)
    if total_issued is None:
        logger.warning(
            "Could not parse Section II 'Balance at close of the month' "
            "(format=%s, page=%d) from %s", fmt, sec_idx, pdf_url,
        )
        return None

    pub_date = _extract_pub_date_from_url(pdf_url)

    return {
        "stock_code": stock_code,
        "company_name": company_name,
        "report_period_date": report_period_date,
        "report_year": report_period_date.year,
        "report_month": report_period_date.month,
        "pub_date": pub_date,
        "shares_issued_excl_treasury": issued,
        "shares_treasury": treasury,
        "shares_total_issued": total_issued,
        "source_pdf_url": pdf_url,
    }
