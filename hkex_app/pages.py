"""Sidebar, routing, and the four workbench pages."""
from datetime import date, timedelta
from typing import List, Optional

import pandas as pd
import streamlit as st

from datalayer.providers.hkex_share_capital import (
    HkexFetchError,
    HkexShareCapitalFetcher,
    normalize_stock_code,
)

from hkex_app.charts import compare_chart, trend_chart
from hkex_app.i18n import LANGUAGE_LABELS, LANGUAGES, get_lang, set_lang, t
from hkex_app.store import HkexShareCapitalStore
from hkex_app.theme import resolve_db_path

# HKEX 证券变动月报表数据下限。实测 00700 的 tier-one 51500 月报表最早
# 出现在 2009 年（11 条），2008 及更早为 0。设 2010 为 UI 下限既满足
# 用户需求，又避免抓取空区间。也用于覆盖 st.date_input 的默认下限
# （value-10年），后者在 2026 默认值下会限制到 2016。
_EARLIEST_DATE = date(2010, 1, 1)

_PAGE_VIEW = "view"
_PAGE_FETCH = "fetch"
_PAGE_COMPARE = "compare"
_PAGE_MANAGE = "manage"

_PAGES = [_PAGE_VIEW, _PAGE_FETCH, _PAGE_COMPARE, _PAGE_MANAGE]
_PAGE_LABEL_KEYS = {
    _PAGE_VIEW: "hkex.nav.view",
    _PAGE_FETCH: "hkex.nav.fetch",
    _PAGE_COMPARE: "hkex.nav.compare",
    _PAGE_MANAGE: "hkex.nav.manage",
}


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------
@st.cache_resource
def _get_store(db_path: str) -> HkexShareCapitalStore:
    return HkexShareCapitalStore(db_path)


def _records_to_df(records: List[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "report_period_date", "pub_date",
                "shares_issued_excl_treasury", "shares_treasury",
                "shares_total_issued", "source_pdf_url",
            ]
        )
    return pd.DataFrame(records)


def _ticker_options(store: HkexShareCapitalStore) -> List[str]:
    rows = store.list_hkex_stock_codes()
    return [r["stock_code"] for r in rows]


# ----------------------------------------------------------------------
# Sidebar & routing
# ----------------------------------------------------------------------
def render_sidebar() -> str:
    """Render the sidebar (language, DB path, navigation) and return the
    selected page key."""
    with st.sidebar:
        # Language switcher
        cur_lang = get_lang()
        lang_idx = LANGUAGES.index(cur_lang) if cur_lang in LANGUAGES else 0
        new_lang = st.selectbox(
            t("hkex.sidebar.language"),
            options=LANGUAGES,
            index=lang_idx,
            format_func=lambda c: LANGUAGE_LABELS.get(c, c),
            key="hkex_lang_select",
        )
        if new_lang != cur_lang:
            set_lang(new_lang)
            st.rerun()

        db_path = resolve_db_path()
        st.caption(f"{t('hkex.sidebar.db_path')}: `{db_path}`")

        page = st.radio(
            t("hkex.sidebar.nav_caption"),
            options=_PAGES,
            format_func=lambda p: t(_PAGE_LABEL_KEYS[p]),
            key="hkex_nav",
        )
    return page


def render_page(page: str) -> None:
    store = _get_store(resolve_db_path())
    if page == _PAGE_VIEW:
        render_view_page(store)
    elif page == _PAGE_FETCH:
        render_fetch_page(store)
    elif page == _PAGE_COMPARE:
        render_compare_page(store)
    elif page == _PAGE_MANAGE:
        render_manage_page(store)
    else:  # pragma: no cover - defensive
        st.error(f"Unknown page: {page}")


# ----------------------------------------------------------------------
# Page 1 — Browse data
# ----------------------------------------------------------------------
def render_view_page(store: HkexShareCapitalStore) -> None:
    st.title(t("hkex.view.title"))

    tickers = _ticker_options(store)
    if not tickers:
        st.info(t("hkex.view.empty"))
        return

    stock = st.selectbox(t("hkex.view.select_ticker"), options=tickers,
                         key="hkex_view_ticker")
    if not stock:
        return

    y_min, y_max = store.get_hkex_year_range(stock)
    if y_min is None or y_max is None:
        st.info(t("hkex.view.empty"))
        return

    if y_min == y_max:
        selected_years = (y_min, y_max)
    else:
        selected_years = st.slider(
            t("hkex.view.year_range"),
            min_value=y_min, max_value=y_max,
            value=(y_min, y_max),
            key="hkex_view_years",
        )

    start = date(selected_years[0], 1, 1)
    end = date(selected_years[1], 12, 31)
    records = store.get_hkex_share_capital_range(stock, start, end)
    df = _records_to_df(records)

    if df.empty:
        st.info(t("hkex.view.no_records", stock=stock))
        return

    company_name = records[0].get("company_name", "") if records else ""
    latest = records[-1]
    earliest = records[0]
    total_latest = latest.get("shares_total_issued") or 0
    total_earliest = earliest.get("shares_total_issued") or 0
    if total_earliest:
        change = (total_latest - total_earliest) / total_earliest
        change_str = f"{change:+.2%}"
    else:
        change_str = "N/A"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("hkex.view.metric.latest_total"), f"{int(total_latest):,}")
    c2.metric(t("hkex.view.metric.change_rate"), change_str)
    c3.metric(t("hkex.view.metric.treasury"),
              f"{int(latest.get('shares_treasury') or 0):,}")
    c4.metric(t("hkex.view.metric.records"), str(len(records)))

    st.plotly_chart(trend_chart(df, stock, company_name), use_container_width=True)

    display_df = df.rename(columns={
        "report_period_date": t("hkex.view.col.period"),
        "pub_date": t("hkex.view.col.pub_date"),
        "shares_issued_excl_treasury": t("hkex.view.col.issued_excl_treasury"),
        "shares_treasury": t("hkex.view.col.treasury"),
        "shares_total_issued": t("hkex.view.col.total_issued"),
        "source_pdf_url": t("hkex.view.col.source"),
    })
    display_df = display_df[[
        t("hkex.view.col.period"), t("hkex.view.col.pub_date"),
        t("hkex.view.col.issued_excl_treasury"), t("hkex.view.col.treasury"),
        t("hkex.view.col.total_issued"), t("hkex.view.col.source"),
    ]]
    st.caption(t("hkex.view.table_caption", n=len(display_df)))
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------
# Page 2 — Fetch data
# ----------------------------------------------------------------------
def _clear_review_state() -> None:
    """Remove all session-state keys created by the fetch review panel."""
    for k in (
        "hkex_pending_records",
        "hkex_pending_stock",
        "hkex_pending_failures",
        "hkex_review_editor",
    ):
        st.session_state.pop(k, None)


def _failures_to_df(failures: List[dict]) -> pd.DataFrame:
    """Build a read-only display DataFrame for parse-failure rows."""
    if not failures:
        return pd.DataFrame(columns=[
            t("hkex.view.col.period"), t("hkex.view.col.source"),
            t("hkex.fetch.review.col_reason"),
        ])
    rows = []
    for f in failures:
        rows.append({
            t("hkex.view.col.period"): f.get("report_period_date"),
            t("hkex.view.col.source"): f.get("source_pdf_url", ""),
            t("hkex.fetch.review.col_reason"): f.get("error", ""),
        })
    return pd.DataFrame(rows)


def _render_review_panel(
    store: HkexShareCapitalStore,
    records: list,
    failures: list,
    code: str,
) -> None:
    """Render the fetch review panel.

    Two tables are shown:
      * **Success table** — a ``st.data_editor`` with a checkbox column so the
        user can select which parsed records to persist. Only rendered when
        ``records`` is non-empty.
      * **Failure table** — a read-only ``st.dataframe`` listing files that
        could not be parsed (with the reason). These cannot be written to the
        DB. Only rendered when ``failures`` is non-empty.

    Records are held in session_state across reruns so the tables survive the
    button clicks that trigger full-page reruns. ``num_rows="fixed"`` keeps the
    index aligned with the ``records`` list, so ``records[i]`` reliably maps to
    row ``i`` of the edited success table.
    """
    # Discard button at the top. A single button renders left-aligned at its
    # content width by default, so no st.columns wrapper is needed.
    if st.button(t("hkex.fetch.review.btn_discard"), key="hkex_review_discard"):
        _clear_review_state()
        st.rerun()

    # ── Success table (selectable for write) ───────────────────────────
    if records:
        select_col = t("hkex.fetch.review.select_col")
        df = _records_to_df(records)
        df.insert(0, select_col, True)  # default: all rows pre-selected
        st.caption(t("hkex.fetch.review.successes_caption", n=len(df)))

        # Only the checkbox column is editable; all data columns are read-only.
        edited = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            disabled=[c for c in df.columns if c != select_col],
            key="hkex_review_editor",
        )
        selected_idx = edited.index[edited[select_col]].tolist()
        n_sel = len(selected_idx)
    else:
        st.info(t("hkex.fetch.review.no_successes"))
        n_sel = 0

    # ── Failure table (read-only) ──────────────────────────────────────
    if failures:
        st.caption(t("hkex.fetch.review.failures_caption", n=len(failures)))
        st.dataframe(_failures_to_df(failures),
                     use_container_width=True, hide_index=True)

    # ── Write controls (only meaningful when there are successes) ──────
    if records:
        # Selected count (left-aligned caption) above the write button.
        st.caption(t("hkex.fetch.review.selected_count",
                     n=n_sel, total=len(records)))

        # Write button below the count. Default width="content" keeps it
        # left-aligned and compact without needing st.columns.
        if st.button(
            t("hkex.fetch.review.btn_save", n=n_sel),
            disabled=(n_sel == 0),
            type="primary",
            key="hkex_review_save",
        ):
            ok = 0
            write_failures: List[str] = []
            for i in selected_idx:
                try:
                    store.save_hkex_share_capital(records[i])
                    ok += 1
                except Exception as exc:  # noqa: BLE001 - per-record resilience
                    write_failures.append(f"{records[i].get('report_period_date')}: {exc}")
            _clear_review_state()
            st.success(t("hkex.fetch.result_ok_write", ok=ok))
            if write_failures:
                st.warning(t("hkex.fetch.result_fail", fail=len(write_failures)))
                for f in write_failures:
                    st.text(f)
            st.rerun()


def render_fetch_page(store: HkexShareCapitalStore) -> None:
    st.title(t("hkex.fetch.title"))

    ticker_input = st.text_input(
        t("hkex.fetch.ticker_label"),
        value="00700.HK",
        key="hkex_fetch_ticker",
    )

    # Live normalization preview
    code: Optional[str] = None
    if ticker_input:
        try:
            code = normalize_stock_code(ticker_input)
            st.success(t("hkex.fetch.normalize_ok", code=code))
        except ValueError as exc:
            st.error(t("hkex.fetch.normalize_bad", exc=str(exc)))

    # Date mode
    mode = st.radio(
        t("hkex.fetch.mode_label"),
        options=["explicit", "incremental"],
        format_func=lambda m: (
            t("hkex.fetch.mode_explicit") if m == "explicit"
            else t("hkex.fetch.mode_incremental")
        ),
        key="hkex_fetch_mode",
    )

    end_default = date.today()
    if mode == "explicit":
        col_a, col_b = st.columns(2)
        start_date = col_a.date_input(t("hkex.fetch.start_label"),
                                      value=date(end_default.year, 1, 1),
                                      min_value=_EARLIEST_DATE,
                                      key="hkex_fetch_start")
        end_date = col_b.date_input(t("hkex.fetch.end_label"),
                                    value=end_default,
                                    min_value=_EARLIEST_DATE,
                                    key="hkex_fetch_end")
    else:
        if code is None:
            st.info(t("hkex.fetch.incr_no_history", stock=ticker_input))
            return
        latest = store.get_latest_hkex_pub_date(code)
        if latest is None:
            st.info(t("hkex.fetch.incr_no_history", stock=code))
            return
        start_date = latest + timedelta(days=1)
        end_date = end_default
        if start_date > end_date:
            st.info(t("hkex.fetch.incr_info", latest=latest,
                      start=start_date, end=end_date))
            st.info(t("hkex.fetch.no_records"))
            return
        st.info(t("hkex.fetch.incr_info", latest=latest,
                  start=start_date, end=end_date))

    # Advanced options
    with st.expander(t("hkex.fetch.advanced")):
        force = st.checkbox(t("hkex.fetch.force"), value=False,
                            help=t("hkex.fetch.force_help"),
                            key="hkex_fetch_force")
        delay = st.number_input(t("hkex.fetch.delay"), min_value=0.0,
                                value=0.5, step=0.1, key="hkex_fetch_delay")
        max_retries = st.number_input(t("hkex.fetch.max_retries"), min_value=1,
                                      value=3, step=1, key="hkex_fetch_retries")

    if code is None or start_date > end_date:
        st.caption(t("hkex.fetch.cli_hint"))
        return

    # Mutual exclusion: if a fetch preview is pending for this ticker, show
    # the review panel instead of the fetch button. Changing the ticker (so
    # `code` no longer matches the stored stock) dismisses the panel. The panel
    # shows when either parsed records OR parse failures are pending — a fully
    # failed fetch still surfaces the failure table to the user.
    pending_records = st.session_state.get("hkex_pending_records")
    pending_failures = st.session_state.get("hkex_pending_failures")
    if (pending_records or pending_failures) \
            and st.session_state.get("hkex_pending_stock") == code:
        _render_review_panel(
            store,
            pending_records or [],
            pending_failures or [],
            code,
        )
        st.caption(t("hkex.fetch.cli_hint"))
        return

    if not st.button(t("hkex.fetch.btn_start"), type="primary",
                     key="hkex_fetch_btn"):
        st.caption(t("hkex.fetch.cli_hint"))
        return

    # Dedup set: mirror hkex_sync.py behavior. Without --force, skip PDFs whose
    # report period is already stored (the review panel then shows only new
    # records). Force re-downloads everything (panel shows the full range,
    # including already-stored periods the user may re-confirm/overwrite).
    # Incremental mode's range already starts past the latest stored pub_date.
    existing_periods = None
    if not force and mode == "explicit":
        existing_periods = store.get_existing_hkex_periods(code)
        if existing_periods:
            st.caption(f"Skipping {len(existing_periods)} already-stored period(s).")

    fetcher = HkexShareCapitalFetcher(delay=float(delay),
                                      max_retries=int(max_retries))
    try:
        with st.spinner(t("hkex.fetch.spinner")):
            records, failures = fetcher.fetch_range_with_failures(
                code, start_date, end_date,
                existing_periods=existing_periods,
            )
    except HkexFetchError as exc:
        st.error(t("hkex.fetch.fetch_error", exc=str(exc)))
        st.caption(t("hkex.fetch.cli_hint"))
        return

    if not records and not failures:
        st.info(t("hkex.fetch.no_records"))
        st.caption(t("hkex.fetch.cli_hint"))
        return

    # Stash records and failures, then rerun so the review panel renders at
    # the top of the page (replacing the fetch button) and survives button
    # clicks. The user then selects which records to persist via the panel's
    # checkboxes; failures are shown read-only.
    _clear_review_state()
    st.session_state["hkex_pending_records"] = records
    st.session_state["hkex_pending_failures"] = failures
    st.session_state["hkex_pending_stock"] = code
    st.rerun()


# ----------------------------------------------------------------------
# Page 3 — Compare tickers
# ----------------------------------------------------------------------
def render_compare_page(store: HkexShareCapitalStore) -> None:
    st.title(t("hkex.compare.title"))

    tickers = _ticker_options(store)
    if len(tickers) < 2:
        st.info(t("hkex.compare.empty"))
        return

    selected = st.multiselect(
        t("hkex.compare.select_tickers"),
        options=tickers,
        key="hkex_compare_tickers",
    )
    if len(selected) < 2:
        st.info(t("hkex.compare.empty"))
        return

    col_a, col_b = st.columns(2)
    start_date = col_a.date_input(t("hkex.compare.date_range"),
                                  value=_EARLIEST_DATE,
                                  min_value=_EARLIEST_DATE,
                                  key="hkex_compare_start")
    end_date = col_b.date_input(t("hkex.compare.date_range"),
                                value=date.today(),
                                min_value=_EARLIEST_DATE,
                                key="hkex_compare_end")

    normalize = st.radio(
        t("hkex.compare.normalize_label"),
        options=[False, True],
        format_func=lambda v: (
            t("hkex.compare.absolute") if not v
            else t("hkex.compare.normalized")
        ),
        key="hkex_compare_normalize",
    )

    frames = []
    for tk in selected:
        recs = store.get_hkex_share_capital_range(tk, start_date, end_date)
        if recs:
            sub = pd.DataFrame(recs)
            sub["ticker"] = tk
            frames.append(sub[["ticker", "report_period_date", "shares_total_issued"]])

    if not frames:
        st.info(t("hkex.compare.no_data"))
        return

    merged = pd.concat(frames, ignore_index=True)
    st.plotly_chart(compare_chart(merged, bool(normalize)),
                    use_container_width=True)
    st.dataframe(merged, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------
# Page 4 — Manage records
# ----------------------------------------------------------------------
def render_manage_page(store: HkexShareCapitalStore) -> None:
    st.title(t("hkex.manage.title"))

    tickers = _ticker_options(store)
    if not tickers:
        st.info(t("hkex.manage.empty"))
        return

    stock = st.selectbox(t("hkex.manage.select_ticker"), options=tickers,
                         key="hkex_manage_ticker")
    if not stock:
        return

    records = store.get_hkex_share_capital_range(stock)
    if not records:
        st.info(t("hkex.manage.no_records", stock=stock))
        return

    df = pd.DataFrame(records)
    display_df = df.rename(columns={
        "report_period_date": t("hkex.manage.col.period"),
        "pub_date": t("hkex.manage.col.pub_date"),
        "shares_total_issued": t("hkex.manage.col.total"),
    })[[
        t("hkex.manage.col.period"), t("hkex.manage.col.pub_date"),
        t("hkex.manage.col.total"),
    ]]
    st.caption(t("hkex.manage.table_caption", n=len(records)))
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # Per-row actions. Iterate the original records so we can build stable keys.
    fetcher = HkexShareCapitalFetcher()
    for rec in records:
        period = rec["report_period_date"]
        total = rec.get("shares_total_issued") or 0
        col_p, col_d, col_r = st.columns([6, 1, 1])
        col_p.text(f"{period}  ·  {int(total):>15,}  ·  {rec.get('source_pdf_url','')}")
        del_key = f"del|{stock}|{period}"
        ref_key = f"ref|{stock}|{period}"
        if col_d.button(t("hkex.manage.btn_delete"), key=del_key):
            try:
                store.delete_hkex_share_capital(stock, period)
                st.success(t("hkex.manage.delete_ok", stock=stock, period=period))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(t("hkex.manage.delete_fail", exc=str(exc)))
        if col_r.button(t("hkex.manage.btn_refetch"), key=ref_key):
            try:
                with st.spinner(t("hkex.fetch.spinner")):
                    refetched = fetcher.fetch_range(
                        stock, period, period, existing_periods=None,
                    )
                if refetched:
                    for r in refetched:
                        store.save_hkex_share_capital(r)
                    st.success(t("hkex.manage.refetch_ok",
                                 stock=stock, period=period))
                else:
                    st.warning(t("hkex.manage.refetch_none",
                                 stock=stock, period=period))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(t("hkex.manage.refetch_fail", exc=str(exc)))

    # Danger zone — clear all records for the ticker.
    with st.expander(t("hkex.manage.danger_zone")):
        confirm = st.checkbox(
            t("hkex.manage.danger_confirm", n=len(records), stock=stock),
            key="hkex_manage_confirm",
        )
        if st.button(t("hkex.manage.btn_clear_all"),
                     disabled=not confirm,
                     type="secondary",
                     key="hkex_manage_clear"):
            try:
                n = store.delete_hkex_share_capital_stock(stock)
                st.success(t("hkex.manage.clear_ok", n=n, stock=stock))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(t("hkex.manage.clear_fail", exc=str(exc)))
