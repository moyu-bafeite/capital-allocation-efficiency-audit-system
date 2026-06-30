"""Database access for the HKEX workbench.

``HkexShareCapitalStore`` subclasses ``DatabaseCache`` and only *adds* new
methods; it never overrides or alters inherited behavior, so the audit app
remains unaffected. The ``hkex_share_capital`` table itself is created by the
parent class' ``_init_db``.
"""
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple

import duckdb

from datalayer.cache import DatabaseCache

# Column order returned by the parent's get_hkex_share_capital — reused so the
# row->dict mapping stays consistent with the rest of the codebase.
_HKEX_COLUMNS = (
    "stock_code",
    "company_name",
    "report_period_date",
    "report_year",
    "report_month",
    "pub_date",
    "shares_issued_excl_treasury",
    "shares_treasury",
    "shares_total_issued",
    "source_pdf_url",
    "fetched_at",
)


def _row_to_dict(row: tuple) -> Dict[str, Any]:
    return {col: val for col, val in zip(_HKEX_COLUMNS, row)}


class HkexShareCapitalStore(DatabaseCache):
    """Extended cache with workbench-specific queries over ``hkex_share_capital``."""

    def list_hkex_stock_codes(self) -> List[Dict[str, str]]:
        """Return all distinct stock codes with a representative company name and
        record count, ordered by stock_code. Used to populate ticker dropdowns."""
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute(
                """
                SELECT stock_code, MAX(company_name) AS company_name, COUNT(*) AS records
                FROM hkex_share_capital
                GROUP BY stock_code
                ORDER BY stock_code
                """
            ).fetchall()
        return [
            {"stock_code": r[0], "company_name": r[1] or "", "records": int(r[2])}
            for r in res
        ]

    def get_hkex_share_capital_range(
        self,
        stock_code: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Return records for a stock within an inclusive [start, end] range over
        ``report_period_date``. ``None`` bounds are open-ended. Ordered ascending."""
        clauses = ["stock_code = ?"]
        params: List[Any] = [stock_code]
        if start is not None:
            clauses.append("report_period_date >= ?")
            params.append(start)
        if end is not None:
            clauses.append("report_period_date <= ?")
            params.append(end)
        where = " AND ".join(clauses)
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute(
                f"""
                SELECT stock_code, company_name, report_period_date, report_year,
                       report_month, pub_date, shares_issued_excl_treasury,
                       shares_treasury, shares_total_issued, source_pdf_url,
                       fetched_at
                FROM hkex_share_capital
                WHERE {where}
                ORDER BY report_period_date
                """,
                params,
            ).fetchall()
        return [_row_to_dict(r) for r in res]

    def get_hkex_year_range(self, stock_code: str) -> Tuple[Optional[int], Optional[int]]:
        """Return (min_report_year, max_report_year) for a stock, or (None, None)."""
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute(
                """
                SELECT MIN(report_year), MAX(report_year)
                FROM hkex_share_capital WHERE stock_code = ?
                """,
                (stock_code,),
            ).fetchone()
        if not res or res[0] is None:
            return None, None
        return int(res[0]), int(res[1])

    def delete_hkex_share_capital(self, stock_code: str, report_period_date: date) -> bool:
        """Delete a single record by (stock_code, report_period_date).

        Returns True if a row was deleted, False if no matching row existed.
        Uses RETURNING to reliably count affected rows (DuckDB rowcount is
        unreliable across versions).
        """
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute(
                """
                DELETE FROM hkex_share_capital
                WHERE stock_code = ? AND report_period_date = ?
                RETURNING report_period_date
                """,
                (stock_code, report_period_date),
            ).fetchall()
        return len(res) > 0

    def delete_hkex_share_capital_stock(self, stock_code: str) -> int:
        """Delete all records for a stock. Returns the number of rows deleted."""
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute(
                """
                DELETE FROM hkex_share_capital
                WHERE stock_code = ?
                RETURNING report_period_date
                """,
                (stock_code,),
            ).fetchall()
        return len(res)
