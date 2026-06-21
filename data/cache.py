import os
import json
import duckdb
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cache")
DB_PATH = os.path.join(DB_DIR, "audit_cache.db")

class DatabaseCache:
    def __init__(self, db_path: str = DB_PATH):
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

    def clear_cache(self):
        """Truncates all tables in the database."""
        with duckdb.connect(self.db_path) as conn:
            conn.execute("DELETE FROM raw_financials")
            conn.execute("DELETE FROM exchange_rates")
            conn.execute("DELETE FROM stock_prices")
            conn.execute("DELETE FROM audit_inputs")

def pd_isna(val) -> bool:
    try:
        import pandas as pd
        return pd.isna(val)
    except ImportError:
        import math
        return val is None or (isinstance(val, float) and math.isnan(val))
