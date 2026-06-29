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
from io import BytesIO
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

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

        :param stock_code: Ticker in any format accepted by normalize_stock_code.
        :param start: Inclusive start date (publication date).
        :param end: Inclusive end date (publication date).
        :param existing_periods: Optional set of report_period_date values
            already stored in the DB. When provided, PDFs whose report period
            (estimated from the URL) is in this set are skipped — avoiding
            redundant downloads for periods already present. Pass None to
            fetch everything (the default, backward-compatible behavior).
        :return: List of record dicts. Each dict has keys: stock_code, company_name,
            report_period_date (date), report_year, report_month, pub_date (date),
            shares_issued_excl_treasury, shares_treasury, shares_total_issued,
            source_pdf_url.
        :raises HkexFetchError: If a non-recoverable error occurs for this ticker.
        """
        code_5 = normalize_stock_code(stock_code)
        logger.info("Fetching HKEX monthly returns for %s (normalized: %s) from %s to %s",
                    stock_code, code_5, start, end)

        stock_id, company_name = self._get_stock_id(code_5)
        logger.debug("Resolved stockId=%s, company_name=%s", stock_id, company_name)

        pdf_links = self._search_monthly_returns(stock_id, start, end)
        logger.info("Found %d monthly return PDF(s) for %s in range", len(pdf_links), code_5)

        # Skip PDFs whose report period is already in the DB (deduplication).
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
                    "Skipping %d already-stored PDF(s); %d to fetch", skipped, len(kept)
                )
            pdf_links = kept

        records: List[Dict[str, object]] = []
        for i, pdf_url in enumerate(pdf_links):
            if i > 0 and self.delay > 0:
                time.sleep(self.delay)
            try:
                rec = self._extract_shares_from_pdf(pdf_url, code_5, company_name)
                if rec is not None:
                    records.append(rec)
                    logger.debug("Parsed %s: %s shares as of %s",
                                 rec["source_pdf_url"], rec["shares_issued_excl_treasury"],
                                 rec["report_period_date"])
            except Exception as exc:
                logger.warning("Failed to parse %s: %s", pdf_url, exc)

        # Sort by report_period_date ascending for deterministic output
        records.sort(key=lambda r: r["report_period_date"])
        return records

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
        for a in soup.select("a[href$='.pdf']"):
            href = a["href"]
            if not href.startswith("http"):
                href = BASE_URL + href
            links.append(href)
        return links

    # ------------------------------------------------------------------
    # Step 3: download & parse a single monthly return PDF
    # ------------------------------------------------------------------
    def _extract_shares_from_pdf(
        self, pdf_url: str, stock_code: str, company_name: str
    ) -> Optional[Dict[str, object]]:
        content = self._get_bytes(pdf_url)
        reader = PdfReader(BytesIO(content))
        if len(reader.pages) < 2:
            logger.warning("PDF has fewer than 2 pages, skipping: %s", pdf_url)
            return None

        page0_text = reader.pages[0].extract_text() or ""
        page1_text = reader.pages[1].extract_text() or ""

        # Report period e.g. "30 November 2024"
        m_period = re.search(
            r"For the month ended:\s*([^\n]+?)\s*Status", page0_text
        )
        period_str = m_period.group(1).strip() if m_period else ""
        report_period_date = _parse_month_ended(period_str)
        if report_period_date is None:
            logger.warning("Could not parse report period '%s' from %s", period_str, pdf_url)
            return None

        # Section II title differs between PDF format versions:
        #   v1.1.1+: "II. Movements in Issued Shares and/or Treasury Shares"
        #            → 3 columns: (issued excl treasury, treasury, total)
        #   v1.0.x : "II. Movements in Issued Shares"
        #            → 1 column: (total issued; treasury concept absent)
        issued_excl_treasury, treasury, total_issued = _parse_section_ii(page1_text)
        if total_issued is None:
            logger.warning("Could not parse section II 'Balance at close of the month' from %s", pdf_url)
            return None

        # Publication date: HKEX PDF URL convention is /YYYY/MMDD/<file>.pdf
        pub_date = _extract_pub_date_from_url(pdf_url)

        return {
            "stock_code": stock_code,
            "company_name": company_name,
            "report_period_date": report_period_date,
            "report_year": report_period_date.year,
            "report_month": report_period_date.month,
            "pub_date": pub_date,
            "shares_issued_excl_treasury": issued_excl_treasury,
            "shares_treasury": treasury,
            "shares_total_issued": total_issued,
            "source_pdf_url": pdf_url,
        }

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
# Module-level parsing helpers
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
    """Parses '30 November 2024' or 'November 30, 2024' into a date.

    Returns the last day of that month (the monthly return always reports
    month-end, so for a parsed (year, month, day) we take the parsed day if
    present, otherwise the last day of the month).
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
    return None


def _extract_pub_date_from_url(pdf_url: str) -> Optional[date]:
    """Extracts the publication date from a HKEX PDF URL.

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


def _parse_section_ii(page1_text: str) -> Tuple[Optional[int], int, Optional[int]]:
    """Parses the "Balance at close of the month" line from Section II.

    Handles two PDF format versions:
      - New (v1.1.1+): "Movements in Issued Shares and/or Treasury Shares"
        → 3 columns: (issued_excl_treasury, treasury, total_issued)
      - Old (v1.0.x): "Movements in Issued Shares"
        → 1 column: (total_issued) — treasury concept did not exist

    Some issuers (e.g. HSBC) report multiple share classes in Section II
    (Ordinary shares then Preference shares). The FF301 form always lists
    Ordinary shares as the first class, so we take the FIRST match on the
    page — which is the primary listed ordinary share count we care about.

    Returns (issued_excl_treasury, treasury, total_issued). In the old format,
    issued_excl_treasury is set equal to total_issued and treasury is 0.
    Returns (None, 0, None) if no match is found.
    """
    # Try the 3-column (new) format first. Take the FIRST match on the page:
    # page 2 only contains Section II, and the first share class listed is
    # invariably Ordinary shares (the primary listed class).
    matches_3 = re.findall(
        r"Balance at close of the month\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)",
        page1_text,
    )
    if matches_3:
        a, b, c = matches_3[0]
        return int(a.replace(",", "")), int(b.replace(",", "")), int(c.replace(",", ""))

    # Fall back to the 1-column (old) format.
    matches_1 = re.findall(
        r"Balance at close of the month\s+([\d,]+)",
        page1_text,
    )
    if matches_1:
        total = int(matches_1[0].replace(",", ""))
        return total, 0, total

    return None, 0, None
