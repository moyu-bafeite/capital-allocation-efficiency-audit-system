import os
import shutil
import unittest
import tempfile
from datetime import date
from typing import Dict, Any, List

from datalayer.cache import DatabaseCache
from datalayer.normalizer import normalize_audit_data
from datalayer.manager import DataManager
from datalayer.providers.base import BaseProvider

class MockProvider(BaseProvider):
    def fetch_financial_data(self, ticker: str, years: List[int]) -> Dict[str, Any]:
        return {
            "ticker": ticker,
            "company_name": "Mock Inc",
            "currency": "USD",
            "amount_unit": "million",
            "market_currency": "USD",
            "exchange_rate_to_reporting_currency": [1.0] * len(years),
            "closing_exchange_rate_to_reporting_currency": [1.0] * len(years),
            "years": years,
            "financials": {
                "net_profit": [100.0] * len(years),
                "ebit": [120.0] * len(years),
                "tax_rate": [0.20] * len(years),
                "interest_expense": [5.0] * len(years),
                "total_equity": [500.0] * len(years),
                "short_term_debt": [50.0] * len(years),
                "long_term_debt": [100.0] * len(years),
                "cash_and_equivalents": [50.0] * len(years),
                "operating_cash_flow": [130.0] * len(years),
                "capex": [40.0] * len(years),
                "da": [20.0] * len(years),
                "dividends_paid": [20.0] * len(years),
                "buybacks_paid": [10.0] * len(years),
                "buybacks_shares": [1.0 * 1e6] * len(years),
                "ma_paid": [5.0] * len(years),
                "goodwill": [10.0] * len(years),
                "shares_outstanding": [100.0 * 1e6] * len(years),
                "avg_stock_price": [10.0] * len(years)
            }
        }

class DataLayerTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_cache.db")
        self.cache = DatabaseCache(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_database_cache_initializes_and_saves_inputs(self):
        sample_input = {
            "ticker": "TEST",
            "provider": "mock",
            "years": [2020, 2021],
            "financials": {
                "net_profit": [100.0, 120.0]
            }
        }
        self.cache.save_audit_input("TEST", "mock", sample_input)
        loaded = self.cache.get_audit_input("TEST", "mock")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["ticker"], "TEST")
        self.assertEqual(loaded["financials"]["net_profit"][1], 120.0)

    def test_database_cache_saves_raw_financials(self):
        years = [2020, 2021]
        financials = {
            "net_profit": [100.0, 120.0],
            "ebit": [120.0, 140.0]
        }
        self.cache.save_raw_financials("TEST", "mock", financials, years)
        loaded = self.cache.get_raw_financials("TEST", "mock", years)
        self.assertEqual(loaded["net_profit"], [100.0, 120.0])
        self.assertEqual(loaded["ebit"], [120.0, 140.0])

    def test_database_cache_saves_prices_and_rates(self):
        self.cache.save_stock_price("TEST", 2020, 15.5)
        self.cache.save_exchange_rate("HKD", "RMB", 2020, 0.85)

        self.assertEqual(self.cache.get_stock_price("TEST", 2020), 15.5)
        self.assertEqual(self.cache.get_exchange_rate("HKD", "RMB", 2020), 0.85)

    def test_normalizer_rectifies_negative_values(self):
        raw_data = {
            "years": [2020, 2021],
            "currency": "USD",
            "amount_unit": "million",
            "market_currency": "USD",
            "exchange_rate_to_reporting_currency": [1.0, 1.0],
            "financials": {
                "net_profit": [100.0, 120.0],
                "tax_rate": [0.20, 1.5], # 1.5 should be clipped
                "capex": [-40.0, -45.0], # should be converted to positive
                "dividends_paid": [20.0, 25.0],
                "buybacks_paid": [0.0, 10.0],
                "buybacks_shares": [0.0, 0.0], # should align
                "shares_outstanding": [-50.0, 100.0], # should fallback
                "avg_stock_price": [10.0, -5.0] # should fallback
            }
        }
        normalized = normalize_audit_data(raw_data)
        self.assertEqual(normalized["financials"]["capex"], [40.0, 45.0])
        self.assertEqual(normalized["financials"]["tax_rate"][1], 1.0)
        self.assertEqual(normalized["financials"]["shares_outstanding"][0], 100000000.0)
        self.assertEqual(normalized["financials"]["avg_stock_price"][1], 10.0)
        self.assertGreater(normalized["financials"]["buybacks_shares"][1], 0.0)

    def test_normalizer_rounds_display_fields_absolute_mode(self):
        raw_data = {
            "years": [2020, 2021],
            "currency": "USD",
            "amount_unit": "absolute",
            "market_currency": "HKD",
            "exchange_rate_to_reporting_currency": [0.8765432109876543, 0.9123456789012345],
            "closing_exchange_rate_to_reporting_currency": [0.8811111111111111, 0.9099999999999999],
            "financials": {
                "net_profit": [100000000.0, 120000000.0],
                "ebit": [120000000.0, 140000000.0],
                "tax_rate": [0.18234567, 0.20987654],
                "avg_stock_price": [12.3456789, 15.9876543],
                "closing_stock_price": [13.1111111, 16.2222222],
                "buybacks_paid": [1234567.891234567, 9876543.219999999],
                "buybacks_shares": [100000.0, 200000.0],
            },
        }
        normalized = normalize_audit_data(raw_data)
        self.assertEqual(normalized["exchange_rate_to_reporting_currency"], [0.8765, 0.9123])
        self.assertEqual(normalized["closing_exchange_rate_to_reporting_currency"], [0.8811, 0.91])
        self.assertEqual(normalized["financials"]["tax_rate"], [0.1823, 0.2099])
        self.assertEqual(normalized["financials"]["avg_stock_price"], [12.346, 15.988])
        self.assertEqual(normalized["financials"]["closing_stock_price"], [13.111, 16.222])
        self.assertEqual(normalized["financials"]["buybacks_paid"], [1234568.0, 9876543.0])

    def test_normalizer_rounds_display_fields_million_mode(self):
        raw_data = {
            "years": [2020, 2021],
            "currency": "USD",
            "amount_unit": "million",
            "market_currency": "HKD",
            "exchange_rate_to_reporting_currency": [0.8765432109876543, 0.9123456789012345],
            "closing_exchange_rate_to_reporting_currency": [0.8811111111111111, 0.9099999999999999],
            "financials": {
                "net_profit": [100.0, 120.0],
                "ebit": [120.0, 140.0],
                "tax_rate": [0.18234567, 0.20987654],
                "avg_stock_price": [12.3456789, 15.9876543],
                "closing_stock_price": [13.1111111, 16.2222222],
                "buybacks_paid": [12.3456789, 9.8765432],
                "buybacks_shares": [100000.0, 200000.0],
            },
        }
        normalized = normalize_audit_data(raw_data)
        self.assertEqual(normalized["exchange_rate_to_reporting_currency"], [0.8765, 0.9123])
        self.assertEqual(normalized["closing_exchange_rate_to_reporting_currency"], [0.8811, 0.91])
        self.assertEqual(normalized["financials"]["tax_rate"], [0.1823, 0.2099])
        self.assertEqual(normalized["financials"]["avg_stock_price"], [12.346, 15.988])
        self.assertEqual(normalized["financials"]["closing_stock_price"], [13.111, 16.222])
        self.assertEqual(normalized["financials"]["buybacks_paid"], [12.345679, 9.876543])

    def test_normalizer_handles_optional_non_cash_adjustment_fields(self):
        # Case A: Fields are completely missing
        raw_data_missing = {
            "years": [2020, 2021],
            "currency": "USD",
            "amount_unit": "million",
            "market_currency": "USD",
            "exchange_rate_to_reporting_currency": [1.0, 1.0],
            "financials": {
                "net_profit": [100.0, 120.0],
            }
        }
        normalized_a = normalize_audit_data(raw_data_missing)
        self.assertIn("impairment_charges", normalized_a["financials"])
        self.assertIn("fair_value_changes", normalized_a["financials"])
        self.assertIn("special_items_of_operating_profit", normalized_a["financials"])
        self.assertEqual(normalized_a["financials"]["impairment_charges"], [0.0, 0.0])
        self.assertEqual(normalized_a["financials"]["fair_value_changes"], [0.0, 0.0])
        self.assertEqual(normalized_a["financials"]["special_items_of_operating_profit"], [0.0, 0.0])

        # Case B: Fields have None or negative values
        raw_data_with_values = {
            "years": [2020, 2021],
            "currency": "USD",
            "amount_unit": "million",
            "market_currency": "USD",
            "exchange_rate_to_reporting_currency": [1.0, 1.0],
            "financials": {
                "net_profit": [100.0, 120.0],
                "impairment_charges": [15.0, None],
                "fair_value_changes": [-10.0, 50.0], # negative values are preserved (losses)
                "special_items_of_operating_profit": [5.0, None],
            }
        }
        normalized_b = normalize_audit_data(raw_data_with_values)
        self.assertEqual(normalized_b["financials"]["impairment_charges"], [15.0, 0.0])
        self.assertEqual(normalized_b["financials"]["fair_value_changes"], [-10.0, 50.0])
        self.assertEqual(normalized_b["financials"]["special_items_of_operating_profit"], [5.0, 0.0])

    def test_data_manager_restores_from_cache_successfully(self):
        # We replace the cache engine of manager and mock provider
        manager = DataManager(self.cache)
        
        # Prepopulate cache
        years = [2020, 2021]
        mock_input = MockProvider().fetch_financial_data("TEST", years)
        manager.cache.save_audit_input("TEST", "futu", mock_input)

        # Call get_audit_input with refresh = False
        res = manager.get_audit_input("TEST", "futu", years, refresh=False)
        self.assertEqual(res.ticker, "TEST")
        self.assertEqual(res.company_name, "Mock Inc")

    def test_data_manager_slices_cached_dict_correctly(self):
        manager = DataManager(self.cache)
        cached_dict = {
            "ticker": "TEST",
            "company_name": "Test Company",
            "currency": "USD",
            "amount_unit": "million",
            "market_currency": "USD",
            "years": [2016, 2017, 2018, 2019, 2020],
            "exchange_rate_to_reporting_currency": [1.0, 1.1, 1.2, 1.3, 1.4],
            "financials": {
                "net_profit": [10.0, 20.0, 30.0, 40.0, 50.0],
                "ebit": [12.0, 22.0, 32.0, 42.0, 52.0]
            }
        }
        
        # Slice for years [2018, 2019, 2020] (indices 2, 3, 4)
        sliced = manager._slice_cached_dict(cached_dict, [2018, 2019, 2020])
        
        self.assertEqual(sliced["years"], [2018, 2019, 2020])
        self.assertEqual(sliced["exchange_rate_to_reporting_currency"], [1.2, 1.3, 1.4])
        self.assertEqual(sliced["financials"]["net_profit"], [30.0, 40.0, 50.0])
        self.assertEqual(sliced["financials"]["ebit"], [32.0, 42.0, 52.0])

        # Slice with invalid/non-existent year should return original dictionary
        sliced_invalid = manager._slice_cached_dict(cached_dict, [2018, 2022])
        self.assertEqual(sliced_invalid, cached_dict)


class HkexSharesEnrichmentTest(unittest.TestCase):
    """Tests for DataManager._enrich_shares_from_hkex — overriding the Futu
    provider's net_profit/EPS shares estimate with authoritative HKEX year-end
    share-capital data when it is present in the DB.
    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_cache.db")
        self.cache = DatabaseCache(self.db_path)
        self.manager = DataManager(self.cache)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _seed_hkex_year_end(self, stock_code, year, total, excl_treasury=None):
        """Insert a December monthly-return record so get_hkex_year_end_shares returns it."""
        rec = {
            "stock_code": stock_code,
            "company_name": "Test",
            "report_period_date": date(year, 12, 31),
            "report_year": year,
            "report_month": 12,
            "pub_date": date(year, 12, 31),
            "shares_issued_excl_treasury": excl_treasury if excl_treasury is not None else total,
            "shares_treasury": 0,
            "shares_total_issued": total,
            "source_pdf_url": f"https://x/{stock_code}/{year}.pdf",
        }
        self.cache.save_hkex_share_capital(rec)

    def _base_data(self, ticker="00700.HK", years=(2020, 2021)):
        return {
            "ticker": ticker,
            "company_name": "T",
            "currency": "HKD",
            "amount_unit": "absolute",
            "market_currency": "HKD",
            "exchange_rate_to_reporting_currency": [1.0] * len(years),
            "closing_exchange_rate_to_reporting_currency": [1.0] * len(years),
            "years": list(years),
            "financials": {
                "shares_outstanding": [111_000_000] * len(years),  # wrong, should be overridden
                "avg_stock_price": [10.0] * len(years),
                "closing_stock_price": [12.0] * len(years),
            },
        }

    def test_overrides_shares_with_hkex_year_end_excl_treasury(self):
        self._seed_hkex_year_end("00700", 2020, total=200_000_000, excl_treasury=190_000_000)
        data = self._base_data()
        self.manager._enrich_shares_from_hkex(data)
        # 2020 overridden to the excl-treasury figure; 2021 (no HKEX data) stays
        self.assertEqual(data["financials"]["shares_outstanding"][0], 190_000_000.0)
        self.assertEqual(data["financials"]["shares_outstanding"][1], 111_000_000)

    def test_falls_back_to_total_issued_when_excl_treasury_missing(self):
        # Legacy monthly returns parsed treasury=0 and excl=total; if excl were
        # 0/None we should fall back to total_issued.
        rec = {
            "stock_code": "00700", "company_name": "T",
            "report_period_date": date(2020, 12, 31), "report_year": 2020,
            "report_month": 12, "pub_date": date(2020, 12, 31),
            "shares_issued_excl_treasury": 0, "shares_treasury": 0,
            "shares_total_issued": 200_000_000, "source_pdf_url": "u",
        }
        self.cache.save_hkex_share_capital(rec)
        data = self._base_data()
        self.manager._enrich_shares_from_hkex(data)
        self.assertEqual(data["financials"]["shares_outstanding"][0], 200_000_000.0)

    def test_no_hkex_data_leaves_shares_untouched(self):
        data = self._base_data()
        original = list(data["financials"]["shares_outstanding"])
        self.manager._enrich_shares_from_hkex(data)
        self.assertEqual(data["financials"]["shares_outstanding"], original)

    def test_unparseable_ticker_does_not_crash(self):
        data = self._base_data(ticker="NOT_A_TICKER")
        # Should return data unchanged without raising.
        self.manager._enrich_shares_from_hkex(data)
        self.assertEqual(data["financials"]["shares_outstanding"][0], 111_000_000)

    def test_loss_year_eps_zero_gets_hkex_override(self):
        # The Futu provider's EPS fallback yields 0.0 for loss years (EPS=0).
        # HKEX override must rescue it rather than the schema's >0 check failing.
        data = self._base_data()
        data["financials"]["shares_outstanding"] = [0.0, 111_000_000]
        self._seed_hkex_year_end("00700", 2020, total=200_000_000)
        self.manager._enrich_shares_from_hkex(data)
        self.assertEqual(data["financials"]["shares_outstanding"][0], 200_000_000.0)


class ClosingStockPriceFallbackTest(unittest.TestCase):
    """Verifies normalizer + schema fill closing_stock_price from avg when absent
    (legacy cached data), so period-end market cap degrades gracefully.
    """
    def test_normalizer_fills_closing_from_avg_when_missing(self):
        from datalayer.normalizer import normalize_audit_data
        raw = {
            "ticker": "00700.HK", "company_name": "T", "currency": "HKD",
            "amount_unit": "absolute", "market_currency": "HKD",
            "exchange_rate_to_reporting_currency": [1.0, 1.0],
            "closing_exchange_rate_to_reporting_currency": [1.0, 1.0],
            "years": [2020, 2021],
            "financials": {
                "shares_outstanding": [100.0, 100.0],
                "avg_stock_price": [10.0, 12.0],
                # closing_stock_price intentionally absent
            },
        }
        out = normalize_audit_data(raw)
        self.assertEqual(out["financials"]["closing_stock_price"], [10.0, 12.0])

    def test_normalizer_fills_closing_from_avg_when_non_positive(self):
        from datalayer.normalizer import normalize_audit_data
        raw = {
            "ticker": "X", "company_name": "T", "currency": "HKD",
            "amount_unit": "absolute", "market_currency": "HKD",
            "exchange_rate_to_reporting_currency": [1.0],
            "closing_exchange_rate_to_reporting_currency": [1.0],
            "years": [2020],
            "financials": {
                "shares_outstanding": [100.0],
                "avg_stock_price": [15.0],
                "closing_stock_price": [0.0],  # non-positive → fallback to avg
            },
        }
        out = normalize_audit_data(raw)
        self.assertEqual(out["financials"]["closing_stock_price"], [15.0])


if __name__ == "__main__":
    unittest.main()
