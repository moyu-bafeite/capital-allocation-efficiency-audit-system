"""HKEX 证券变动月报表抓取模块.

从香港交易所披露易 (HKEXnews) 抓取上市公司根据《上市规则》第 13.51B 条
提交的"证券变动月报表" (Monthly Return for Equity Issuer on Movements
in Securities, 文件类别 tier-one code 51500), 解析 PDF 中第 II 部分的
已发行股本变动数据, 返回结构化记录.

该模块为纯抓取层, 不涉及数据库写入. 调用方 (例如 scripts/hkex_sync.py)
负责将返回的记录通过 DatabaseCache.save_hkex_share_capital 持久化.

主要接口:
    fetcher = HkexShareCapitalFetcher()
    records = fetcher.fetch_range("00700", date(2024, 1, 1), date(2024, 12, 31))
"""
import json
import logging
import re
import time
import calendar
from datetime import date, datetime
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

from datalayer.providers.hkex_pdf_parser import _extract_pub_date_from_url

logger = logging.getLogger(__name__)

BASE_URL = "https://www1.hkexnews.hk"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

# tier-one category code for "月報表" (Monthly Return)
TIER_ONE_MONTHLY_RETURN = "51500"


class HkexFetchError(Exception):
    """Raised when HKEX fetching fails in a way that should abort the current ticker."""


def normalize_stock_code(ticker: str) -> str:
    """Normalize various ticker formats to a 5-digit HKEX code string.

    Accepts '00700', '700', '00700.HK', '0700.HK', 'HK.00700' etc.
    Returns the zero-padded 5-digit code, e.g. '00700'.
    """
    t = ticker.strip().upper()
    # Strip market suffixes: '00700.HK', 'HK.00700', '00700.HI'
    for sep in (".", "/"):
        if sep in t:
            parts = t.split(sep)
            # 'HK.00700' -> take last part; '00700.HK' -> take first part
            if parts[0] == "HK":
                t = parts[-1]
            else:
                t = parts[0]
            break
    if not t.isdigit():
        raise ValueError(
            f"Cannot parse HKEX stock code from '{ticker}'. "
            f"Expected formats: '00700', '700', '00700.HK', 'HK.00700'."
        )
    return t.zfill(5)


class HkexShareCapitalFetcher:
    """Fetches HKEX monthly return share-capital data for a single stock.

    The fetcher is stateless across tickers; reuse one instance for multiple
    tickers to benefit from connection reuse in the underlying requests.Session.

    :param delay: Seconds to sleep between PDF downloads (polite rate limiting).
    :param max_retries: Number of retry attempts for transient network errors.
    :param timeout: HTTP timeout in seconds for each request.
    """

    def __init__(self, delay: float = 0.5, max_retries: int = 3, timeout: float = 30.0):
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_range(
        self,
        stock_code: str,
        start: date,
        end: date,
        existing_periods: Optional[Set[date]] = None,
    ) -> List[Dict[str, object]]:
        """Fetch all monthly return records whose publication date falls in [start, end].

        Backward-compatible wrapper around :meth:`fetch_range_with_failures`
        that discards the failure list. New callers wanting parse-failure
        details should call ``fetch_range_with_failures`` directly.

        :return: List of successfully parsed record dicts (see
            :meth:`fetch_range_with_failures` for the dict shape).
        :raises HkexFetchError: If a non-recoverable error occurs for this ticker.
        """
        records, _failures = self.fetch_range_with_failures(
            stock_code, start, end, existing_periods=existing_periods,
        )
        return records

    def fetch_range_with_failures(
        self,
        stock_code: str,
        start: date,
        end: date,
        existing_periods: Optional[Set[date]] = None,
    ) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
        """Fetch monthly returns in [start, end]; return parsed records AND failures.

        Same behavior as :meth:`fetch_range`, but instead of silently dropping
        PDFs/DOCs that fail to parse (only logging a warning), it returns them
        as a second list so callers (CLI dry-run table, UI review panel) can
        surface them to the user.

        :param stock_code: Ticker in any format accepted by normalize_stock_code.
        :param start: Inclusive start date (publication date).
        :param end: Inclusive end date (publication date).
        :param existing_periods: Optional set of report_period_date values
            already stored in the DB. When provided, files whose report period
            (estimated from the URL) is in this set are skipped — avoiding
            redundant downloads for periods already present. Pass None to
            fetch everything (the default).
        :return: Tuple ``(records, failures)``.
            * ``records``: successfully parsed dicts with keys stock_code,
              company_name, report_period_date (date), report_year,
              report_month, pub_date (date|None), shares_issued_excl_treasury,
              shares_treasury, shares_total_issued, source_pdf_url.
            * ``failures``: dicts for files that could not be parsed, with keys
              stock_code, company_name, source_pdf_url, report_period_date
              (date|None, estimated from URL), report_month (int|None),
              error (str). These cannot be persisted.
        :raises HkexFetchError: If a non-recoverable error occurs for this ticker
            (e.g. stockId lookup or search fails).
        """
        code_5 = normalize_stock_code(stock_code)
        logger.info("Fetching HKEX monthly returns for %s (normalized: %s) from %s to %s",
                    stock_code, code_5, start, end)

        stock_id, company_name = self._get_stock_id(code_5)
        logger.debug("Resolved stockId=%s, company_name=%s", stock_id, company_name)

        pdf_links = self._search_monthly_returns(stock_id, start, end)
        logger.info("Found %d monthly return file(s) for %s in range", len(pdf_links), code_5)

        # Skip files whose report period is already in the DB (deduplication).
        # The estimate uses the publication date encoded in the URL; the actual
        # report period is confirmed only after parsing, but the URL-based
        # estimate is reliable enough to avoid the download for already-stored
        # periods. Anything we cannot estimate is fetched to be safe.
        if existing_periods is not None:
            kept: List[str] = []
            skipped = 0
            for url in pdf_links:
                est = _estimate_report_period_from_url(url)
                if est is not None and est in existing_periods:
                    skipped += 1
                    logger.debug("Skipping already-stored report period %s: %s", est, url)
                    continue
                kept.append(url)
            if skipped:
                logger.info(
                    "Skipping %d already-stored file(s); %d to fetch", skipped, len(kept)
                )
            pdf_links = kept

        records: List[Dict[str, object]] = []
        failures: List[Dict[str, object]] = []
        for i, pdf_url in enumerate(pdf_links):
            if i > 0 and self.delay > 0:
                time.sleep(self.delay)
            try:
                rec = self._extract_shares_from_pdf_or_doc(pdf_url, code_5, company_name)
                if rec is not None:
                    records.append(rec)
                    logger.debug("Parsed %s: %s shares as of %s",
                                 rec["source_pdf_url"], rec["shares_issued_excl_treasury"],
                                 rec["report_period_date"])
                else:
                    # Parser returned None (e.g. couldn't locate Section II).
                    est = _estimate_report_period_from_url(pdf_url)
                    failures.append({
                        "stock_code": code_5,
                        "company_name": company_name,
                        "source_pdf_url": pdf_url,
                        "report_period_date": est,
                        "report_month": est.month if est is not None else None,
                        "error": "parse returned None",
                    })
                    logger.warning("Failed to parse %s: parse returned None", pdf_url)
            except Exception as exc:
                logger.warning("Failed to parse %s: %s", pdf_url, exc)
                est = _estimate_report_period_from_url(pdf_url)
                failures.append({
                    "stock_code": code_5,
                    "company_name": company_name,
                    "source_pdf_url": pdf_url,
                    "report_period_date": est,
                    "report_month": est.month if est is not None else None,
                    "error": str(exc),
                })

        # Sort by report_period_date ascending for deterministic output.
        # Failures with a None estimate sort first (earliest).
        records.sort(key=lambda r: r["report_period_date"])
        failures.sort(key=lambda f: (f["report_period_date"] is None,
                                     f["report_period_date"] or date.min))
        return records, failures

    # ------------------------------------------------------------------
    # Step 1: stockId lookup via prefix.do JSONP endpoint
    # ------------------------------------------------------------------
    def _get_stock_id(self, code_5: str) -> Tuple[int, str]:
        url = f"{BASE_URL}/search/prefix.do"
        params = {
            "lang": "ZH",
            "type": "A",
            "name": code_5,
            "market": "SEHK",
            "callback": "cb",
        }
        text = self._get_text(url, params=params)
        m = re.search(r"callback\((.*)\);?\s*$", text, re.DOTALL)
        if not m:
            raise HkexFetchError(f"prefix.do response is not valid JSONP for {code_5}")
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            raise HkexFetchError(f"prefix.do JSON parse failed for {code_5}: {exc}")
        for s in data.get("stockInfo", []):
            if s.get("code") == code_5:
                return int(s["stockId"]), s.get("name", "")
        raise HkexFetchError(f"stockId not found for code {code_5}")

    # ------------------------------------------------------------------
    # Step 2: search titlesearch.xhtml for monthly return PDFs
    # ------------------------------------------------------------------
    def _search_monthly_returns(self, stock_id: int, start: date, end: date) -> List[str]:
        # The HKEX title search is a JSF form POST. We first GET the page to
        # obtain a fresh JSESSIONID cookie and javax.faces.ViewState token,
        # then POST the search form.
        page_url = f"{BASE_URL}/search/titlesearch.xhtml?lang=zh"
        page_html = self._get_text(page_url)

        m_jsess = re.search(r"jsessionid=([A-Za-z0-9_.]+)", page_html)
        jsessionid = m_jsess.group(1) if m_jsess else None

        m_vs = re.search(
            r'name="javax.faces.ViewState"[^>]*value="([^"]+)"', page_html
        )
        if not m_vs:
            raise HkexFetchError("Could not extract javax.faces.ViewState from search page")
        view_state = m_vs.group(1)

        action_url = f"{BASE_URL}/search/titlesearch.xhtml"
        if jsessionid:
            action_url += f";jsessionid={jsessionid}"

        # The search form expects YYYYMMDD strings for from/to.
        from_str = start.strftime("%Y%m%d")
        to_str = end.strftime("%Y%m%d")
        # The HKEX search UI restricts unfiltered-by-stock queries to small
        # date ranges, but with a stockId + tier-one category the range can
        # span up to 12 months per request. We chunk longer ranges into
        # yearly windows to stay within the server limit.
        all_links: List[str] = []
        window_start = start
        while window_start <= end:
            if window_start.year < end.year:
                window_end = date(window_start.year, 12, 31)
            else:
                window_end = end

            links = self._search_window(
                action_url, view_state, stock_id, window_start, window_end
            )
            all_links.extend(links)
            # Advance to next year
            window_start = date(window_start.year + 1, 1, 1)

        # De-duplicate while preserving order
        seen = set()
        unique: List[str] = []
        for link in all_links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        return unique

    def _search_window(
        self, action_url: str, view_state: str, stock_id: int, start: date, end: date
    ) -> List[str]:
        from_str = start.strftime("%Y%m%d")
        to_str = end.strftime("%Y%m%d")
        form_data = {
            "j_idt10": "j_idt10",
            "j_idt10:loadMoreRange": "100",
            "startDate": "",
            "endDate": "",
            "stockId": str(stock_id),
            "stockCode": "",
            "searchType": "1",
            "searchTypeInt": "1",
            "newsTitle": "",
            "tierOneId": TIER_ONE_MONTHLY_RETURN,
            "tierTwoId": "-2",
            "tierTwoGpId": "-2",
            "selectedDocType": "-2",
            "selectedSecurities": "0",
            "displayResultTable": "block",
            "titleSearchResultControl.searchByIndex": "0",
            "titleSearchByAllResult.dateFromUi": "",
            "titleSearchByAllResult.dateToUi": "",
            "market": "SEHK",
            "from": from_str,
            "to": to_str,
            "t1code": TIER_ONE_MONTHLY_RETURN,
            "t2code": "-2",
            "t2Gcode": "-2",
            "documentType": "-2",
            "category": "0",
            "javax.faces.ViewState": view_state,
        }
        html = self._post_text(action_url, data=form_data)
        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        # Include .doc alongside .pdf: a minority of small issuers (e.g. 00837)
        # uploaded Word .doc files instead of PDFs for the legacy period. The
        # parser routes by extension; .doc is handled by hkex_doc_parser.
        for a in soup.select("a[href$='.pdf'], a[href$='.doc']"):
            href = a["href"]
            if not href.startswith("http"):
                href = BASE_URL + href
            links.append(href)
        return links

    # ------------------------------------------------------------------
    # Step 3: download & parse a single monthly return (PDF or DOC)
    # ------------------------------------------------------------------
    def _extract_shares_from_pdf_or_doc(
        self, doc_url: str, stock_code: str, company_name: str
    ) -> Optional[Dict[str, object]]:
        """Download a monthly-return file and parse its share-capital data.

        Routes by URL extension: ``.doc`` → :mod:`hkex_doc_parser`, otherwise
        (``.pdf``) → :mod:`hkex_pdf_parser` (which auto-detects FF301 新版 /
        March 2019 旧版). Thin bridge between the HTTP layer
        (``self._get_bytes``) and the pure-parsing modules.
        """
        content = self._get_bytes(doc_url)
        if doc_url.lower().endswith(".doc"):
            from datalayer.providers.hkex_doc_parser import parse_share_capital_doc
            return parse_share_capital_doc(content, stock_code, company_name, doc_url)
        from datalayer.providers.hkex_pdf_parser import parse_share_capital_pdf
        return parse_share_capital_pdf(content, stock_code, company_name, doc_url)

    # ------------------------------------------------------------------
    # HTTP helpers with retry
    # ------------------------------------------------------------------
    def _get_text(self, url: str, params: Optional[dict] = None) -> str:
        r = self._request("GET", url, params=params)
        return r.text

    def _post_text(self, url: str, data: Optional[dict] = None) -> str:
        r = self._request("POST", url, data=data)
        return r.text

    def _get_bytes(self, url: str) -> bytes:
        r = self._request("GET", url)
        return r.content

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.debug(
                        "Request %s %s failed (attempt %d/%d): %s. Retrying in %.1fs",
                        method, url, attempt, self.max_retries, exc, backoff,
                    )
                    time.sleep(backoff)
        raise HkexFetchError(f"{method} {url} failed after {self.max_retries} attempts: {last_exc}")


# ----------------------------------------------------------------------
# Module-level helpers
# ----------------------------------------------------------------------
# PDF parsing helpers (_MONTH_NAMES, _parse_month_ended, _parse_section_ii,
# _extract_pub_date_from_url, parse_share_capital_pdf) live in
# datalayer.providers.hkex_pdf_parser. Only the URL-based report-period
# estimator remains here, used by fetch_range for download deduplication.
def _estimate_report_period_from_url(pdf_url: str) -> Optional[date]:
    """Estimates the report period (month-end) from a monthly return PDF URL.

    HKEX monthly returns are filed in the first few days of the month following
    the report period. A PDF published on YYYY-MM-DD therefore reports on the
    last day of the *previous* month, e.g. pub 2026-01-05 → report 2025-12-31.

    Returns the last day of that previous month (computed via
    calendar.monthrange so February/leap-year is handled correctly), or None
    if the publication date cannot be parsed from the URL.
    """
    pub = _extract_pub_date_from_url(pdf_url)
    if pub is None:
        return None
    # A January publication reflects the prior December.
    if pub.month == 1:
        rp_year, rp_month = pub.year - 1, 12
    else:
        rp_year, rp_month = pub.year, pub.month - 1
    _, last_day = calendar.monthrange(rp_year, rp_month)
    return date(rp_year, rp_month, last_day)
