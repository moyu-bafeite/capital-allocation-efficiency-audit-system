import os
import json
import duckdb
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Set, Union

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, ".cache", "audit.db")
DATABASE_URL = os.environ.get("DATABASE_URL", _DEFAULT_DB_PATH)

class DatabaseCache:
    def __init__(self, db_path: str = DATABASE_URL):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with duckdb.connect(self.db_path) as conn:
            # Table 1: Raw Financials from statements
            conn.execute("""
                CREATE TABLE IF NOT EXISTS raw_financials (
                    ticker VARCHAR,
                    provider VARCHAR,
                    year INTEGER,
                    field_name VARCHAR,
                    field_value DOUBLE,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (ticker, provider, year, field_name)
                )
            """)

            # Table 2: Historical Exchange Rates
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    from_currency VARCHAR,
                    to_currency VARCHAR,
                    year INTEGER,
                    rate DOUBLE,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (from_currency, to_currency, year)
                )
            """)

            # Table 2b: Historical Closing Exchange Rates
            conn.execute("""
                CREATE TABLE IF NOT EXISTS closing_exchange_rates (
                    from_currency VARCHAR,
                    to_currency VARCHAR,
                    year INTEGER,
                    rate DOUBLE,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (from_currency, to_currency, year)
                )
            """)

            # Table 3: Historical Stock Prices
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    ticker VARCHAR,
                    year INTEGER,
                    price DOUBLE,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (ticker, year)
                )
            """)

            # Table 4: Cached Company Audit Input Document
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_inputs (
                    ticker VARCHAR,
                    provider VARCHAR,
                    data_json VARCHAR,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (ticker, provider)
                )
            """)

            # Table 5: HKEX Monthly Return share capital movements
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hkex_share_capital (
                    stock_code VARCHAR,
                    company_name VARCHAR,
                    report_period_date DATE,
                    report_year INTEGER,
                    report_month INTEGER,
                    pub_date DATE,
                    shares_issued_excl_treasury BIGINT,
                    shares_treasury BIGINT,
                    shares_total_issued BIGINT,
                    source_pdf_url VARCHAR,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (stock_code, report_period_date)
                )
            """)

    def save_raw_financials(self, ticker: str, provider: str, financials_dict: Dict[str, List[float]], years: List[int]):
        """
        Saves raw financials into financials table.
        financials_dict has structure like: {"net_profit": [100.0, 120.0, ...]}
        """
        now = datetime.now()
        with duckdb.connect(self.db_path) as conn:
            for field, values in financials_dict.items():
                for year, val in zip(years, values):
                    if val is None or pd_isna(val):
                        continue
                    conn.execute("""
                        INSERT OR REPLACE INTO raw_financials (ticker, provider, year, field_name, field_value, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (ticker, provider, int(year), field, float(val), now))

    def get_raw_financials(self, ticker: str, provider: str, years: List[int]) -> Dict[str, List[float]]:
        """
        Retrieves raw financials for specific years.
        Returns a dict of fields and their aligned values.
        """
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT year, field_name, field_value 
                FROM raw_financials 
                WHERE ticker = ? AND provider = ? AND year IN (SELECT UNNEST(?))
            """, (ticker, provider, [int(year) for year in years])).fetchall()
            
        # Reconstruct aligned lists
        year_idx = {year: idx for idx, year in enumerate(years)}
        fields_data = {}
        for r_year, field, val in res:
            if field not in fields_data:
                fields_data[field] = [0.0] * len(years)
            if r_year in year_idx:
                fields_data[field][year_idx[r_year]] = val
        return fields_data

    def save_exchange_rate(self, from_curr: str, to_curr: str, year: int, rate: float):
        now = datetime.now()
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO exchange_rates (from_currency, to_currency, year, rate, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (from_curr, to_curr, int(year), float(rate), now))

    def get_exchange_rate(self, from_curr: str, to_curr: str, year: int) -> Optional[float]:
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT rate FROM exchange_rates 
                WHERE from_currency = ? AND to_currency = ? AND year = ?
            """, (from_curr, to_curr, int(year))).fetchone()
            return res[0] if res else None

    def save_closing_exchange_rate(self, from_curr: str, to_curr: str, year: int, rate: float):
        now = datetime.now()
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO closing_exchange_rates (from_currency, to_currency, year, rate, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (from_curr, to_curr, int(year), float(rate), now))

    def get_closing_exchange_rate(self, from_curr: str, to_curr: str, year: int) -> Optional[float]:
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT rate FROM closing_exchange_rates 
                WHERE from_currency = ? AND to_currency = ? AND year = ?
            """, (from_curr, to_curr, int(year))).fetchone()
            return res[0] if res else None

    def save_stock_price(self, ticker: str, year: int, price: float):
        now = datetime.now()
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO stock_prices (ticker, year, price, fetched_at)
                VALUES (?, ?, ?, ?)
            """, (ticker, int(year), float(price), now))

    def get_stock_price(self, ticker: str, year: int) -> Optional[float]:
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT price FROM stock_prices WHERE ticker = ? AND year = ?
            """, (ticker, int(year))).fetchone()
            return res[0] if res else None

    def save_audit_input(self, ticker: str, provider: str, input_dict: Dict[str, Any]):
        now = datetime.now()
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO audit_inputs (ticker, provider, data_json, fetched_at)
                VALUES (?, ?, ?, ?)
            """, (ticker, provider, json.dumps(input_dict, ensure_ascii=False), now))

    def get_audit_input(self, ticker: str, provider: str) -> Optional[Dict[str, Any]]:
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT data_json FROM audit_inputs WHERE ticker = ? AND provider = ?
            """, (ticker, provider)).fetchone()
            return json.loads(res[0]) if res else None

    def save_hkex_share_capital(self, record: Dict[str, Any]):
        """Upserts a single HKEX monthly return record into hkex_share_capital.

        Expected record keys: stock_code, company_name, report_period_date (date/dict/str),
        report_year, report_month, pub_date (date/dict/str/None),
        shares_issued_excl_treasury, shares_treasury, shares_total_issued, source_pdf_url.
        """
        now = datetime.now()
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO hkex_share_capital
                    (stock_code, company_name, report_period_date, report_year, report_month,
                     pub_date, shares_issued_excl_treasury, shares_treasury, shares_total_issued,
                     source_pdf_url, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["stock_code"],
                record.get("company_name"),
                _to_duck_date(record.get("report_period_date")),
                int(record["report_year"]),
                int(record["report_month"]),
                _to_duck_date(record.get("pub_date")),
                int(record["shares_issued_excl_treasury"]),
                int(record.get("shares_treasury", 0)),
                int(record.get("shares_total_issued", 0)),
                record.get("source_pdf_url"),
                now,
            ))

    def get_hkex_share_capital(self, stock_code: str, year: int) -> List[Dict[str, Any]]:
        """Retrieves all monthly return records for a stock in a given year, ordered by report_period_date."""
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT stock_code, company_name, report_period_date, report_year, report_month,
                       pub_date, shares_issued_excl_treasury, shares_treasury, shares_total_issued,
                       source_pdf_url, fetched_at
                FROM hkex_share_capital
                WHERE stock_code = ? AND report_year = ?
                ORDER BY report_month
            """, (stock_code, int(year))).fetchall()
        return [
            {
                "stock_code": r[0], "company_name": r[1],
                "report_period_date": r[2], "report_year": r[3], "report_month": r[4],
                "pub_date": r[5], "shares_issued_excl_treasury": r[6],
                "shares_treasury": r[7], "shares_total_issued": r[8],
                "source_pdf_url": r[9], "fetched_at": r[10],
            }
            for r in res
        ]

    def get_latest_hkex_pub_date(self, stock_code: str) -> Optional[date]:
        """Returns the latest pub_date (as datetime.date) for a stock, or None if no records exist."""
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT MAX(pub_date) FROM hkex_share_capital WHERE stock_code = ?
            """, (stock_code,)).fetchone()
        return res[0] if res and res[0] is not None else None

    def get_hkex_year_end_shares(self, stock_code: str, year: int) -> Optional[Dict[str, Any]]:
        """Returns the year-end share capital record (report_month=12 preferred, else 11), or None."""
        records = self.get_hkex_share_capital(stock_code, year)
        if not records:
            return None
        for r in records:
            if r["report_month"] == 12:
                return r
        for r in records:
            if r["report_month"] == 11:
                return r
        return None

    def get_existing_hkex_periods(self, stock_code: str) -> Set[date]:
        """Returns the set of all report_period_date values stored for a stock.

        Used by the sync script to skip re-downloading PDFs for report periods
        already present in the DB (deduplication by primary key).
        """
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute("""
                SELECT report_period_date FROM hkex_share_capital WHERE stock_code = ?
            """, (stock_code,)).fetchall()
        return {r[0] for r in res if r[0] is not None}

    def clear_cache(self):
        """Truncates all tables in the database."""
        with duckdb.connect(self.db_path) as conn:
            conn.execute("DELETE FROM raw_financials")
            conn.execute("DELETE FROM exchange_rates")
            conn.execute("DELETE FROM closing_exchange_rates")
            conn.execute("DELETE FROM stock_prices")
            conn.execute("DELETE FROM audit_inputs")
            conn.execute("DELETE FROM hkex_share_capital")

def _to_duck_date(val) -> Optional[Union[date, str]]:
    """Normalizes a date-ish value to something DuckDB accepts for a DATE column.

    Accepts datetime.date, datetime.datetime, dict with 'year'/'month'/'day',
    or a string 'YYYY-MM-DD'. Returns None for None.
    """
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) else val.date()
    if isinstance(val, dict):
        try:
            return date(int(val["year"]), int(val["month"]), int(val["day"]))
        except (KeyError, ValueError):
            return None
    if isinstance(val, str):
        return val.strip() or None
    return val

def pd_isna(val) -> bool:
    try:
        import pandas as pd
        return pd.isna(val)
    except ImportError:
        import math
        return val is None or (isinstance(val, float) and math.isnan(val))
