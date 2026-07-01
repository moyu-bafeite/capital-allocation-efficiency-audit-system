"""Self-contained i18n for the HKEX workbench.

Intentionally does NOT import the root ``i18n`` package so the sub-app remains
independently portable. Mechanism mirrors the root ``i18n.i18n`` module for
zero learning cost; the translation catalog only holds ``hkex.*`` keys.

Language state is stored in ``st.session_state["hkex_lang"]`` (separate from
the audit app's ``"lang"`` key) so the two apps never clash if run together.
"""
from __future__ import annotations

LANGUAGES = ["en", "zh"]
DEFAULT_LANG = "en"
LANGUAGE_LABELS = {"zh": "繁體中文", "en": "English"}

TRANSLATIONS = {
    # ── app / sidebar ──────────────────────────────────────────────────
    "hkex.app.title": {
        "en": "HKEX Share Capital Workbench",
        "zh": "HKEX 股本變動工作臺",
    },
    "hkex.sidebar.nav_caption": {
        "en": "WORKBENCH",
        "zh": "工作臺",
    },
    "hkex.sidebar.language": {
        "en": "Language",
        "zh": "語言",
    },
    "hkex.sidebar.db_path": {
        "en": "DuckDB path",
        "zh": "DuckDB 路徑",
    },
    "hkex.nav.view": {"en": "Browse data", "zh": "查看數據"},
    "hkex.nav.fetch": {"en": "Fetch data", "zh": "抓取數據"},
    "hkex.nav.compare": {"en": "Compare tickers", "zh": "多 Ticker 對比"},
    "hkex.nav.manage": {"en": "Manage records", "zh": "記錄管理"},

    # ── view page ──────────────────────────────────────────────────────
    "hkex.view.title": {"en": "Browse share-capital data", "zh": "已入庫股本數據瀏覽"},
    "hkex.view.select_ticker": {"en": "Ticker", "zh": "股票代碼"},
    "hkex.view.year_range": {"en": "Year range", "zh": "年份範圍"},
    "hkex.view.empty": {
        "en": "Database is empty. Go to the **Fetch data** page to pull data first.",
        "zh": "數據庫為空，請先到「抓取數據」頁拉取數據。",
    },
    "hkex.view.no_records": {
        "en": "No records in the selected range for {stock}.",
        "zh": "{stock} 在所選區間內無記錄。",
    },
    "hkex.view.metric.latest_total": {
        "en": "Latest total issued",
        "zh": "最新總髮行股數",
    },
    "hkex.view.metric.change_rate": {
        "en": "Change vs earliest",
        "zh": "較最早一期變化",
    },
    "hkex.view.metric.treasury": {
        "en": "Latest treasury shares",
        "zh": "最新庫存股數",
    },
    "hkex.view.metric.records": {"en": "Records", "zh": "記錄條數"},
    "hkex.view.table_caption": {
        "en": "Detail ({n} rows)",
        "zh": "明細（{n} 條）",
    },
    "hkex.view.col.period": {"en": "Period end", "zh": "報告期末"},
    "hkex.view.col.pub_date": {"en": "Pub date", "zh": "發佈日期"},
    "hkex.view.col.issued_excl_treasury": {
        "en": "Issued (excl. treasury)",
        "zh": "已發行(不含庫存)",
    },
    "hkex.view.col.treasury": {"en": "Treasury", "zh": "庫存股"},
    "hkex.view.col.total_issued": {"en": "Total issued", "zh": "總髮行"},
    "hkex.view.col.source": {"en": "Source PDF", "zh": "來源 PDF"},

    # ── fetch page ─────────────────────────────────────────────────────
    "hkex.fetch.title": {"en": "Fetch monthly returns", "zh": "抓取證券變動月報表"},
    "hkex.fetch.ticker_label": {"en": "Ticker", "zh": "股票代碼"},
    "hkex.fetch.normalize_ok": {
        "en": "Normalized code: `{code}`",
        "zh": "規範化代碼：`{code}`",
    },
    "hkex.fetch.normalize_bad": {
        "en": "Cannot parse ticker: {exc}",
        "zh": "無法解析股票代碼：{exc}",
    },
    "hkex.fetch.mode_label": {"en": "Date mode", "zh": "日期模式"},
    "hkex.fetch.mode_explicit": {"en": "Explicit range", "zh": "顯式日期範圍"},
    "hkex.fetch.mode_incremental": {
        "en": "Incremental (since last record)",
        "zh": "增量(從最新記錄次日)",
    },
    "hkex.fetch.start_label": {"en": "Start date", "zh": "起始日期"},
    "hkex.fetch.end_label": {"en": "End date", "zh": "結束日期"},
    "hkex.fetch.incr_info": {
        "en": "Latest stored pub_date = {latest}. Will fetch **{start} → {end}**.",
        "zh": "當前最新 pub_date = {latest}，將抓取 **{start} → {end}**。",
    },
    "hkex.fetch.incr_no_history": {
        "en": "No prior record for {stock}. Use **Explicit range** to backfill first.",
        "zh": "{stock} 無歷史記錄，請先用「顯式日期範圍」回填。",
    },
    "hkex.fetch.advanced": {"en": "Advanced options", "zh": "高級選項"},
    "hkex.fetch.force": {"en": "Force re-fetch", "zh": "強制重抓"},
    "hkex.fetch.force_help": {
        "en": "Re-download and upsert even for report periods already stored.",
        "zh": "對已入庫的報告期也重新下載並覆蓋。",
    },
    "hkex.fetch.delay": {"en": "Delay between PDFs (s)", "zh": "PDF 間隔(秒)"},
    "hkex.fetch.max_retries": {"en": "Max retries", "zh": "最大重試次數"},
    "hkex.fetch.btn_start": {"en": "Start fetch", "zh": "開始抓取"},
    "hkex.fetch.spinner": {"en": "Fetching PDFs from HKEXnews…", "zh": "正在從 HKEXnews 抓取 PDF…"},
    "hkex.fetch.result_ok_write": {
        "en": "Fetched and wrote {ok} record(s) to DB.",
        "zh": "抓取並寫入 {ok} 條記錄到數據庫。",
    },
    "hkex.fetch.result_fail": {
        "en": "{fail} record(s) failed to persist.",
        "zh": "{fail} 條記錄入庫失敗。",
    },
    "hkex.fetch.no_records": {
        "en": "No monthly returns found in the range.",
        "zh": "區間內未找到月報表。",
    },
    "hkex.fetch.fetch_error": {"en": "Fetch failed: {exc}", "zh": "抓取失敗：{exc}"},
    "hkex.fetch.cli_hint": {
        "en": "For multi-year backfills, prefer `scripts/hkex_sync.py` CLI to avoid long UI blocking.",
        "zh": "大區間全量回填建議仍用 `scripts/hkex_sync.py` CLI，避免 UI 長時間阻塞。",
    },
    "hkex.fetch.preview_caption": {
        "en": "Preview ({n} records)",
        "zh": "預覽（{n} 條）",
    },
    "hkex.fetch.review.select_col": {"en": "Save?", "zh": "寫入?"},
    "hkex.fetch.review.btn_save": {
        "en": "Save selected ({n}) to DB",
        "zh": "將選中 {n} 條寫入數據庫",
    },
    "hkex.fetch.review.btn_discard": {"en": "Discard", "zh": "放棄"},
    "hkex.fetch.review.selected_count": {
        "en": "{n}/{total} selected",
        "zh": "已選 {n}/{total} 條",
    },
    "hkex.fetch.review.failures_caption": {
        "en": "Failed to parse ({n}) — cannot be written to DB",
        "zh": "解析失敗（{n} 條）— 無法入庫",
    },
    "hkex.fetch.review.col_reason": {"en": "Reason", "zh": "原因"},
    "hkex.fetch.review.no_successes": {
        "en": "No records parsed successfully.",
        "zh": "無成功解析的記錄。",
    },
    "hkex.fetch.review.successes_caption": {
        "en": "Parsed successfully ({n})",
        "zh": "成功解析（{n} 條）",
    },

    # ── compare page ───────────────────────────────────────────────────
    "hkex.compare.title": {"en": "Compare tickers", "zh": "多 Ticker 對比"},
    "hkex.compare.select_tickers": {"en": "Tickers (2–5)", "zh": "股票代碼（2–5 個）"},
    "hkex.compare.date_range": {"en": "Common date range", "zh": "公共日期範圍"},
    "hkex.compare.normalize_label": {"en": "Scale", "zh": "量綱"},
    "hkex.compare.absolute": {"en": "Absolute", "zh": "絕對值"},
    "hkex.compare.normalized": {"en": "Normalized (first=100)", "zh": "歸一化(首期=100)"},
    "hkex.compare.empty": {
        "en": "Select at least 2 tickers with data.",
        "zh": "請選擇至少 2 個有數據的 ticker。",
    },
    "hkex.compare.no_data": {
        "en": "No data for the selected tickers/range.",
        "zh": "所選 ticker 在該區間無數據。",
    },

    # ── manage page ────────────────────────────────────────────────────
    "hkex.manage.title": {"en": "Manage records", "zh": "記錄管理"},
    "hkex.manage.select_ticker": {"en": "Ticker", "zh": "股票代碼"},
    "hkex.manage.empty": {
        "en": "Database is empty.",
        "zh": "數據庫為空。",
    },
    "hkex.manage.no_records": {
        "en": "No records for {stock}.",
        "zh": "{stock} 暫無記錄。",
    },
    "hkex.manage.table_caption": {
        "en": "All records ({n})",
        "zh": "全部記錄（{n} 條）",
    },
    "hkex.manage.btn_delete": {"en": "Delete", "zh": "刪除"},
    "hkex.manage.btn_refetch": {"en": "Refetch", "zh": "重抓"},
    "hkex.manage.delete_ok": {
        "en": "Deleted {stock} @ {period}.",
        "zh": "已刪除 {stock} @ {period} 的記錄。",
    },
    "hkex.manage.delete_fail": {"en": "Delete failed: {exc}", "zh": "刪除失敗：{exc}"},
    "hkex.manage.refetch_ok": {
        "en": "Refetched and overwrote {stock} @ {period}.",
        "zh": "已重抓並覆蓋 {stock} @ {period} 的記錄。",
    },
    "hkex.manage.refetch_fail": {"en": "Refetch failed: {exc}", "zh": "重抓失敗：{exc}"},
    "hkex.manage.refetch_none": {
        "en": "Refetch returned no record for {stock} @ {period}.",
        "zh": "重抓未取到 {stock} @ {period} 的記錄。",
    },
    "hkex.manage.danger_zone": {"en": "Danger zone", "zh": "危險區"},
    "hkex.manage.danger_confirm": {
        "en": "I confirm: clear all {n} record(s) for {stock}.",
        "zh": "我確認要清空 {stock} 的全部 {n} 條記錄。",
    },
    "hkex.manage.btn_clear_all": {
        "en": "Clear all records for this ticker",
        "zh": "清空該 Ticker 全部記錄",
    },
    "hkex.manage.clear_ok": {
        "en": "Cleared {n} record(s) for {stock}.",
        "zh": "已清空 {stock} 的 {n} 條記錄。",
    },
    "hkex.manage.clear_fail": {"en": "Clear failed: {exc}", "zh": "清空失敗：{exc}"},
    "hkex.manage.col.period": {"en": "Period end", "zh": "報告期末"},
    "hkex.manage.col.pub_date": {"en": "Pub date", "zh": "發佈日期"},
    "hkex.manage.col.total": {"en": "Total issued", "zh": "總髮行"},
    "hkex.manage.col.actions": {"en": "Actions", "zh": "操作"},

    # ── charts ─────────────────────────────────────────────────────────
    "hkex.chart.trend_title": {
        "en": "{stock} share-capital trend",
        "zh": "{stock} 股本變動趨勢",
    },
    "hkex.chart.compare_title": {
        "en": "Total issued shares comparison",
        "zh": "總髮行股本對比",
    },
    "hkex.chart.normalized_title": {
        "en": "Normalized (first=100)",
        "zh": "歸一化(首期=100)",
    },
    "hkex.chart.axis.date": {"en": "Report period", "zh": "報告期"},
    "hkex.chart.axis.shares": {"en": "Shares", "zh": "股數"},
    "hkex.chart.axis.index": {"en": "Index (first=100)", "zh": "指數(首期=100)"},
    "hkex.chart.legend.issued_excl_treasury": {
        "en": "Issued (excl. treasury)",
        "zh": "已發行(不含庫存)",
    },
    "hkex.chart.legend.treasury": {"en": "Treasury", "zh": "庫存股"},
    "hkex.chart.legend.total_issued": {"en": "Total issued", "zh": "總髮行"},
}


def get_lang() -> str:
    """Return the active language code, defaulting to ``DEFAULT_LANG``."""
    try:
        import streamlit as st

        if "hkex_lang" not in st.session_state:
            st.session_state["hkex_lang"] = DEFAULT_LANG
        return st.session_state["hkex_lang"]
    except Exception:
        return DEFAULT_LANG


def set_lang(lang: str) -> None:
    """Persist the active language in Streamlit session state."""
    try:
        import streamlit as st

        st.session_state["hkex_lang"] = lang if lang in LANGUAGES else DEFAULT_LANG
    except Exception:
        pass


def t(key: str, **kwargs) -> str:
    """Look up ``key`` in the workbench catalog for the active language.

    Supports ``str.format`` templates. Missing keys fall back to the key itself.
    """
    lang = get_lang()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    val = entry.get(lang, entry.get(DEFAULT_LANG, key))
    try:
        return val.format(**kwargs) if kwargs else val
    except Exception:
        return val
