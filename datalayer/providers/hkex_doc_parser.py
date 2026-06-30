"""HKEX 月报表 .doc 文件解析模块（纯解析，无网络）.

少数小发行人（如 00837 譚木匠）在 2021 年之前直接上传 Microsoft Word
.doc 文件而非 PDF。这些 .doc 是真正的二进制 OLE2 格式（magic D0CF11E0，
content-type application/msword），不是 HTML/RTF 伪装。

由于 HKEX 月报表的正文是英文/数字，``latin-1`` 解码即可提取出全部表单
文本（表格单元格以 ``\\x07`` BEL 字符分隔）。提取并归一后的文本结构与
旧版 (March 2019) PDF 完全一致——同样是 "II. Movements in Issued Share
Capital"、DD/MM/YYYY 报告期、4 列布局——故本模块直接复用
:mod:`hkex_pdf_parser` 的 legacy 解析函数，不重复实现正则逻辑。

无需外部依赖（antiword / libreoffice / python-docx 均不需要）。

公开接口:
    from datalayer.providers.hkex_doc_parser import parse_share_capital_doc
    record = parse_share_capital_doc(doc_bytes, "00837", "譚木匠", url)
"""
import logging
import re
from typing import Dict, Optional

from datalayer.providers.hkex_pdf_parser import (
    _extract_pub_date_from_url,
    _parse_report_period_legacy,
    _parse_section_ii_legacy,
)

logger = logging.getLogger(__name__)

# Word .doc 用 \x07 (BEL) 分隔表格单元格，归一为空格后即可走 legacy 正则。
_CELL_SEP = "\x07"


def _extract_doc_text(doc_bytes: bytes) -> str:
    """Decode a binary .doc into a workable text string.

    HKEX monthly-return .doc files embed the form text as ASCII/latin-1 with
    table cells separated by ``\\x07`` (BEL). We decode the whole blob as
    latin-1 (errors ignored — non-ASCII bytes e.g. in issuer Chinese names
    are not needed for the form fields we parse) and normalize BEL to spaces.
    """
    text = doc_bytes.decode("latin-1", errors="ignore")
    return text.replace(_CELL_SEP, " ")


def parse_share_capital_doc(
    doc_bytes: bytes,
    stock_code: str,
    company_name: str,
    doc_url: str,
) -> Optional[Dict[str, object]]:
    """Parse a single HKEX monthly-return .doc into a share-capital record.

    The .doc form structure is identical to the legacy (March 2019) PDF
    format, so report-period and Section II parsing are delegated to
    :mod:`hkex_pdf_parser`'s legacy helpers. Section II is located as the
    text span between ``II. Movements in Issued Share Capital`` and the next
    ``III.`` heading (the .doc is a single text blob, not paginated).

    :param doc_bytes: Raw .doc file content (binary).
    :param stock_code: Normalized 5-digit stock code (e.g. "00837").
    :param company_name: Issuer name (from stockId lookup).
    :param doc_url: Source URL (used for pub_date extraction & audit trail).
    :return: Record dict (same shape as ``parse_share_capital_pdf``) or None.
    """
    text = _extract_doc_text(doc_bytes)

    # Report period (legacy DD/MM/YYYY format)
    report_period_date = _parse_report_period_legacy(text)
    if report_period_date is None:
        logger.warning("Could not parse report period from .doc %s", doc_url)
        return None

    # Section II block: from "II. Movements in Issued Share Capital" to next "III."
    i = text.find("II. Movements in Issued Share Capital")
    if i < 0:
        logger.warning("Could not locate Section II heading in .doc %s", doc_url)
        return None
    j = text.find("III.", i + 5)
    section_text = text[i:j] if j > i else text[i:i + 1500]

    issued, treasury, total_issued = _parse_section_ii_legacy(section_text)
    if total_issued is None:
        logger.warning(
            "Could not parse Section II 'Balance at close of the month' from .doc %s",
            doc_url,
        )
        return None

    pub_date = _extract_pub_date_from_url(doc_url)

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
        "source_pdf_url": doc_url,
    }
