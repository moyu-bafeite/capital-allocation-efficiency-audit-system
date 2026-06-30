#!/usr/bin/env python3
"""hkex_sync.py — Sync HKEX monthly-return share-capital data into the local DB.

This is a standalone command-line tool designed to run both interactively and
as a periodic (cron) job. It fetches "证券变动月报表" (Monthly Return for
Equity Issuer on Movements in Securities) from HKEXnews for one or more HK
stocks and persists the parsed share-capital figures into the
`hkex_share_capital` DuckDB table.

Examples
--------
# Full backfill for Tencent over a publication-date range
python scripts/hkex_sync.py --ticker 00700.HK --start 2024-01-01 --end 2024-12-31

# Incremental cronjob run: resume from the latest stored publication date
python scripts/hkex_sync.py --ticker 00700.HK --since-last

# Batch over a watchlist file (one ticker per line)
python scripts/hkex_sync.py --tickers-file watchlist.txt --since-last

# Dry run: fetch & print, do not write to DB
python scripts/hkex_sync.py --ticker 00700.HK --start 2024-01-01 --end 2024-12-31 --dry-run

Exit codes
----------
0  All tickers processed successfully (zero failures).
1  At least one ticker failed (partial success). Check logs for details.
2  Configuration / argument error.
"""
import argparse
import logging
import os
import sys
from datetime import date, timedelta
from typing import List, Optional, Tuple

# Make project root importable when the script is run directly.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datalayer.cache import DatabaseCache  # noqa: E402
from datalayer.providers.hkex_share_capital import (  # noqa: E402
    HkexFetchError,
    HkexShareCapitalFetcher,
    normalize_stock_code,
)

logger = logging.getLogger("hkex_sync")

# Exit codes
EXIT_OK = 0
EXIT_PARTIAL_FAILURE = 1
EXIT_CONFIG_ERROR = 2


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="hkex_sync",
        description=(
            "Fetch HKEX monthly-return share-capital data and store it in the "
            "local DuckDB cache. Suitable as a cron job."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Ticker selection (mutually exclusive group)
    ticker_group = p.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        "--ticker",
        help="Single ticker, e.g. '00700.HK' or '00700'.",
    )
    ticker_group.add_argument(
        "--tickers",
        help="Comma-separated list of tickers, e.g. '00700,00005,0388'.",
    )
    ticker_group.add_argument(
        "--tickers-file",
        help="Path to a file with one ticker per line (blank lines and '#' comments ignored).",
    )

    # Date range (required unless --since-last)
    p.add_argument(
        "--start",
        help="Inclusive start date (publication date), YYYY-MM-DD.",
    )
    p.add_argument(
        "--end",
        help="Inclusive end date (publication date), YYYY-MM-DD. Defaults to today.",
    )

    p.add_argument(
        "--since-last",
        action="store_true",
        help=(
            "Incremental mode: for each ticker, look up the latest pub_date in "
            "the DB and fetch from the next day. Errors out if no prior record "
            "exists for a ticker (use --start/--end for the initial backfill). "
            "--end may be supplied to cap the upper bound (defaults to today)."
        ),
    )

    # Storage
    p.add_argument(
        "--db-path",
        default=None,
        help=(
            "Path to the DuckDB file. Defaults to the DATABASE_URL env var "
            "or .cache/audit.db under the project root."
        ),
    )

    # Behavior
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print records without writing to the database.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help=(
            "Re-fetch and upsert even for report periods already present in "
            "the DB. Use this to capture amended filings. By default, periods "
            "already stored are skipped (no redundant download)."
        ),
    )
    p.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to sleep between PDF downloads (polite rate limiting). Default: 0.5.",
    )
    p.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="HTTP retry attempts for transient network errors. Default: 3.",
    )

    # Logging
    p.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging.")
    p.add_argument("-q", "--quiet", action="store_true", help="Only emit WARNING+ logs.")

    return p.parse_args(argv)


def _parse_date(s: str, arg_name: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        logger.error("Invalid --%s value '%s'. Expected YYYY-MM-DD.", arg_name, s)
        sys.exit(EXIT_CONFIG_ERROR)


def _load_tickers(args: argparse.Namespace) -> List[str]:
    if args.ticker:
        return [args.ticker]
    if args.tickers:
        return [t.strip() for t in args.tickers.split(",") if t.strip()]
    if args.tickers_file:
        if not os.path.isfile(args.tickers_file):
            logger.error("Tickers file not found: %s", args.tickers_file)
            sys.exit(EXIT_CONFIG_ERROR)
        out = []
        with open(args.tickers_file, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                out.append(line)
        if not out:
            logger.error("Tickers file %s contains no valid tickers.", args.tickers_file)
            sys.exit(EXIT_CONFIG_ERROR)
        return out
    # Should be unreachable due to argparse mutual-exclusion required=True
    logger.error("No ticker source provided.")
    sys.exit(EXIT_CONFIG_ERROR)


def _resolve_date_range(
    args: argparse.Namespace, cache: DatabaseCache, stock_code: str
) -> Tuple[date, date]:
    """Returns (start, end) for the given stock, accounting for --since-last."""
    end_date = _parse_date(args.end, "end") if args.end else date.today()

    if args.since_last:
        if args.start:
            logger.error(
                "--since-last cannot be combined with --start. Pick one mode. "
                "(--end is allowed as an optional upper bound.)"
            )
            sys.exit(EXIT_CONFIG_ERROR)
        latest = cache.get_latest_hkex_pub_date(stock_code)
        if latest is None:
            logger.error(
                "--since-last requested for %s but no prior record exists in DB. "
                "Run once with --start/--end to backfill before using --since-last.",
                stock_code,
            )
            raise HkexFetchError(f"No prior record for {stock_code}")
        start_date = latest + timedelta(days=1)
        if start_date > end_date:
            logger.info(
                "[%s] DB is already up to date (latest pub_date=%s, today=%s). Nothing to do.",
                stock_code, latest, end_date,
            )
            return None, None
        logger.info("[%s] Incremental from %s to %s (last stored pub_date=%s)",
                    stock_code, start_date, end_date, latest)
        return start_date, end_date

    # Explicit --start required when not --since-last
    if not args.start:
        logger.error("--start is required when --since-last is not set.")
        sys.exit(EXIT_CONFIG_ERROR)
    start_date = _parse_date(args.start, "start")
    if start_date > end_date:
        logger.error("--start (%s) is after --end (%s).", start_date, end_date)
        sys.exit(EXIT_CONFIG_ERROR)
    return start_date, end_date


def _process_ticker(
    ticker: str,
    args: argparse.Namespace,
    fetcher: HkexShareCapitalFetcher,
    cache: DatabaseCache,
) -> Tuple[int, int]:
    """Process a single ticker. Returns (records_fetched, records_failed).

    records_failed counts PDFs that could not be parsed; ticker-level errors
    raise and are caught by the caller.
    """
    stock_code = normalize_stock_code(ticker)
    logger.info("=== Processing %s (stock_code=%s) ===", ticker, stock_code)

    start_date, end_date = _resolve_date_range(args, cache, stock_code)
    if start_date is None:
        # Already up to date in --since-last mode
        return 0, 0

    # Build the dedup set: skip PDFs whose report period is already in the DB.
    # Skipped entirely for: --force (user wants to refresh), --dry-run (the
    # table is meant to show the full requested range), and --since-last (the
    # date range itself already starts after the latest stored pub_date).
    existing_periods = None
    if not args.force and not args.dry_run and not args.since_last:
        existing_periods = cache.get_existing_hkex_periods(stock_code)
        if existing_periods:
            logger.info(
                "[%s] %d report period(s) already in DB; will skip re-downloading them.",
                stock_code, len(existing_periods),
            )

    records, failures = fetcher.fetch_range_with_failures(
        stock_code, start_date, end_date, existing_periods=existing_periods
    )
    if not records and not failures:
        logger.info("[%s] No monthly returns found in range %s..%s.",
                    stock_code, start_date, end_date)
        return 0, 0

    written = 0
    failed = 0
    if args.dry_run:
        company_name = (records[0].get("company_name") if records
                        else failures[0].get("company_name") if failures else "")
        print(_format_records_table(records, failures, stock_code, company_name))
        written = len(records)
        failed = len(failures)
    else:
        for rec in records:
            try:
                cache.save_hkex_share_capital(rec)
                written += 1
            except Exception as exc:
                logger.warning("[%s] Failed to persist record for %s: %s",
                               stock_code, rec["report_period_date"], exc)
                failed += 1
        # Parse failures (files that could not be parsed at all) are counted
        # separately so the summary reflects both parse failures and DB-write
        # failures. They are already logged by fetch_range_with_failures.
        failed += len(failures)

    logger.info(
        "[%s] Done: %d records %s, %d failed.",
        stock_code,
        written,
        "fetched (dry-run)" if args.dry_run else "written to DB",
        failed,
    )
    return written, failed


# ----------------------------------------------------------------------
# Dry-run table rendering
# ----------------------------------------------------------------------
# (header, key, align, format_func)
_TABLE_COLUMNS = [
    ("Status", "_status", "left", lambda v: str(v)),
    ("Mo", "report_month", "left", lambda v: f"{int(v):02d}" if v is not None else "—"),
    ("PeriodEnd", "report_period_date", "left", lambda v: str(v) if v is not None else "—"),
    ("PubDate", "pub_date", "left", lambda v: str(v) if v is not None else "—"),
    ("Issued(excl treas)", "shares_issued_excl_treasury", "right",
     lambda v: f"{int(v):,}" if v is not None else "—"),
    ("Treasury", "shares_treasury", "right",
     lambda v: f"{int(v):,}" if v is not None else "—"),
    ("Total Issued", "shares_total_issued", "right",
     lambda v: f"{int(v):,}" if v is not None else "—"),
    ("Source PDF", "source_pdf_url", "left", lambda v: str(v) if v is not None else ""),
    ("Reason", "_reason", "left", lambda v: str(v) if v else ""),
]


def _format_records_table(
    records: list,
    failures: list,
    stock_code: str,
    company_name: str,
) -> str:
    """Render parsed records AND parse failures as one Unicode-bordered table.

    Pass rows carry share counts; Failed rows show "—" for the numeric columns
    and the parse error in the Reason column. Rows are merged and sorted by
    ``report_period_date`` ascending (failures with a None estimate sort
    first), so pass/fail rows for the same period interleave for easy
    diagnosis. ``stock_code`` and ``company_name`` are shown in the caption
    line (constant across all rows of a single ticker).
    """
    n_pass = len(records)
    n_fail = len(failures)
    name_part = f" ({company_name})" if company_name else ""
    caption = (f"=== {stock_code}{name_part} — {n_pass} pass, "
               f"{n_fail} failed (dry-run) ===")

    if n_pass == 0 and n_fail == 0:
        return caption + "\n(no records)"

    # Build a unified row list. Each row is a dict carrying the column keys
    # plus _status ("Pass"/"Failed") and _reason (error string for failures).
    all_rows: List[dict] = []
    for rec in records:
        row = dict(rec)
        row["_status"] = "Pass"
        row["_reason"] = ""
        all_rows.append(row)
    for f in failures:
        # Failures lack pub_date and share fields; default them to None so the
        # format funcs render "—" uniformly.
        row = {
            "stock_code": f.get("stock_code"),
            "company_name": f.get("company_name"),
            "report_period_date": f.get("report_period_date"),
            "report_month": f.get("report_month"),
            "pub_date": None,
            "shares_issued_excl_treasury": None,
            "shares_treasury": None,
            "shares_total_issued": None,
            "source_pdf_url": f.get("source_pdf_url"),
            "_status": "Failed",
            "_reason": f.get("error", ""),
        }
        all_rows.append(row)

    # Sort by report_period_date ascending; None (un-estimable) sorts last.
    all_rows.sort(key=lambda r: (r["report_period_date"] is None,
                                 r["report_period_date"] or date.min))

    # Format every cell so column widths reflect the rendered strings.
    rendered: List[List[str]] = []
    for row in all_rows:
        rendered.append([fmt(row.get(key)) for (_, key, _, fmt) in _TABLE_COLUMNS])

    headers = [h for (h, _, _, _) in _TABLE_COLUMNS]
    aligns = [a for (_, _, a, _) in _TABLE_COLUMNS]

    # Compute column widths: max of header and all cells in that column.
    col_widths = []
    for col_idx, header in enumerate(headers):
        cell_w = max(len(row[col_idx]) for row in rendered) if rendered else 0
        col_widths.append(max(len(header), cell_w))

    def _pad(cell: str, width: int, align: str) -> str:
        return cell.rjust(width) if align == "right" else cell.ljust(width)

    def _row(cells: List[str], align_override: Optional[str] = None) -> str:
        inner = "│".join(
            " " + _pad(c, w, align_override or a) + " "
            for c, w, a in zip(cells, col_widths, aligns)
        )
        return "│" + inner + "│"

    top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    sep = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    bottom = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

    # Headers are always left-aligned regardless of the data alignment.
    lines = [caption, top, _row(headers, align_override="left"), sep]
    lines.extend(_row(row) for row in rendered)
    lines.append(bottom)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.verbose else (logging.WARNING if args.quiet else logging.INFO)
    # Log to stdout (not the default stderr) so that log lines and the
    # dry-run table — which is also printed to stdout — interleave in
    # chronological order instead of being split across two streams.
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    tickers = _load_tickers(args)
    logger.info("Tickers to process: %s", tickers)

    # Resolve DB path
    db_path = args.db_path or os.environ.get("DATABASE_URL") or os.path.join(
        _PROJECT_ROOT, ".cache", "audit.db"
    )
    logger.info("Using DuckDB at %s (dry_run=%s)", db_path, args.dry_run)

    cache = DatabaseCache(db_path) if not args.dry_run else _DryRunCache(db_path)
    fetcher = HkexShareCapitalFetcher(
        delay=args.delay, max_retries=args.max_retries
    )

    total_fetched = 0
    total_failed = 0
    tickers_ok = 0
    tickers_failed = 0

    for ticker in tickers:
        try:
            f, fail = _process_ticker(ticker, args, fetcher, cache)
            total_fetched += f
            total_failed += fail
            tickers_ok += 1
        except HkexFetchError as exc:
            logger.error("[%s] Aborted: %s", ticker, exc)
            tickers_failed += 1
        except Exception as exc:
            logger.exception("[%s] Unexpected error: %s", ticker, exc)
            tickers_failed += 1

    # Final summary
    summary = (
        f"Processed {len(tickers)} ticker(s): "
        f"{tickers_ok} ok, {tickers_failed} failed, "
        f"{total_fetched} records fetched, {total_failed} record failures."
    )
    if tickers_failed == 0 and total_failed == 0:
        logger.info(summary)
        return EXIT_OK
    else:
        logger.warning(summary)
        return EXIT_PARTIAL_FAILURE


class _DryRunCache:
    """A no-op cache stand-in for --dry-run mode.

    Instantiating DatabaseCache would still create the DB file; this avoids
    touching storage at all in dry-run mode. We only need
    get_latest_hkex_pub_date for --since-last support, so we proxy that
    one method to a real DatabaseCache lazily.
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._real: Optional[DatabaseCache] = None

    def get_latest_hkex_pub_date(self, stock_code: str):
        if self._real is None:
            self._real = DatabaseCache(self._db_path)
        return self._real.get_latest_hkex_pub_date(stock_code)

    def get_existing_hkex_periods(self, stock_code: str):
        if self._real is None:
            self._real = DatabaseCache(self._db_path)
        return self._real.get_existing_hkex_periods(stock_code)

    def save_hkex_share_capital(self, record):
        # No-op in dry-run
        pass


if __name__ == "__main__":
    sys.exit(main())
