from typing import List, Dict, Any, Optional
import logging
from models.input_schema import CompanyAuditInput
from datalayer.cache import DatabaseCache
from datalayer.normalizer import normalize_audit_data
from datalayer.providers.futu import FutuOpenDProvider

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, db_cache: Optional[DatabaseCache] = None):
        self.cache = db_cache or DatabaseCache()

    def _enrich_shares_from_hkex(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Override shares_outstanding with authoritative HKEX year-end data.

        HKEX monthly returns disclose the exact issued-share count at month-end;
        the December (or November) return gives the year-end outstanding shares
        (``shares_issued_excl_treasury`` = issued minus treasury = the figure
        entitled to earnings, i.e. true shares outstanding). This is more
        rigorous than the Futu provider's ``net_profit / EPS`` back-calculation
        (which is rounded, a weighted-average, and breaks for loss years).

        Called on BOTH the cache-hit and refresh paths so that freshly-fetched
        HKEX monthly-return data is reflected even without a forced refresh of
        the Futu pull. When HKEX data is not in the DB, the provider's fallback
        value is left untouched.

        :param data: The raw/cached audit-input dict (mutated in place).
        :return: The same dict with shares_outstanding overridden where HKEX
            year-end data is available.
        """
        from datalayer.providers.hkex_share_capital import normalize_stock_code

        try:
            stock_code = normalize_stock_code(data["ticker"])
        except (ValueError, KeyError):
            return data  # ticker missing or unparseable — leave shares as-is

        financials = data.get("financials", {})
        shares_list = financials.get("shares_outstanding")
        years = data.get("years", [])
        if not shares_list or not years:
            return data

        overridden = 0
        for i, year in enumerate(years):
            rec = self.cache.get_hkex_year_end_shares(stock_code, year)
            if rec is None:
                continue
            # Prefer issued-excl-treasury (true outstanding); fall back to total
            # issued for legacy returns where the treasury concept was absent.
            shares = rec.get("shares_issued_excl_treasury")
            if not shares:
                shares = rec.get("shares_total_issued")
            if shares and shares > 0:
                shares_list[i] = float(shares)
                overridden += 1
        if overridden:
            logger.info(
                "Overrode shares_outstanding for %s with HKEX year-end data "
                "(%d/%d years).", stock_code, overridden, len(years),
            )
        return data

    def _slice_cached_dict(self, cached_dict: Dict[str, Any], requested_years: List[int]) -> Dict[str, Any]:
        """Slices the cached dictionary to include only the requested years."""
        cached_years = cached_dict.get("years", [])
        try:
            indices = [cached_years.index(y) for y in requested_years]
        except ValueError:
            return cached_dict

        sliced = cached_dict.copy()
        sliced["years"] = requested_years
        
        for root_field in ["exchange_rate_to_reporting_currency", "closing_exchange_rate_to_reporting_currency"]:
            if root_field in sliced and isinstance(sliced[root_field], list):
                if len(sliced[root_field]) == len(cached_years):
                    sliced[root_field] = [sliced[root_field][i] for i in indices]

        if "financials" in sliced:
            sliced_fin = sliced["financials"].copy()
            for k, v in sliced_fin.items():
                if isinstance(v, list) and len(v) == len(cached_years):
                    sliced_fin[k] = [v[i] for i in indices]
            sliced["financials"] = sliced_fin
            
        return sliced

    def get_audit_input(self, ticker: str, provider_name: str, years: List[int], refresh: bool = False) -> CompanyAuditInput:
        """
        Retrieves the CompanyAuditInput from the cache or pulls it from the specified provider API.
        
        :param ticker: Stock ticker/symbol (e.g. '0388.HK')
        :param provider_name: Provider name ('futu')
        :param years: List of integer fiscal years.
        :param refresh: If True, forces a fresh API call and updates the cache.
        :return: A validated CompanyAuditInput object.
        """
        provider_name = provider_name.lower().strip()
        ticker = ticker.strip()

        # 1. Check local DuckDB cache if refresh is False
        if not refresh:
            cached_dict = self.cache.get_audit_input(ticker, provider_name)
            if cached_dict:
                # Double-check years align with cached dictionary.
                # If cached years match requested years, use it.
                if set(years).issubset(set(cached_dict.get("years", []))):
                    sliced_dict = self._slice_cached_dict(cached_dict, years)
                    # Re-inject authoritative HKEX year-end shares (in case the
                    # user fetched HKEX monthly returns after the Futu pull was
                    # cached, so the cached shares become authoritative without
                    # requiring a forced refresh).
                    self._enrich_shares_from_hkex(sliced_dict)
                    return CompanyAuditInput(**sliced_dict)

        # 2. Instantiate correct API provider
        if provider_name == "futu":
            provider = FutuOpenDProvider()
        else:
            raise ValueError(f"Unknown data provider: '{provider_name}'. Supported providers: 'futu'")

        # 3. Pull raw data from API
        raw_data = provider.fetch_financial_data(ticker, years)

        # 3b. Override shares_outstanding with authoritative HKEX year-end data
        # (issued excl. treasury) when the monthly-return data is in the DB.
        self._enrich_shares_from_hkex(raw_data)

        # 4. Standardize and normalize data fields
        normalized_data = normalize_audit_data(raw_data)

        # 5. Validate with Pydantic Schema
        validated_input = CompanyAuditInput(**normalized_data)

        # 6. Persist to DuckDB local cache
        # Save raw financials
        self.cache.save_raw_financials(
            ticker=ticker,
            provider=provider_name,
            financials_dict=normalized_data["financials"],
            years=years
        )
        
        # Save stock prices
        for yr, p in zip(years, normalized_data["financials"]["avg_stock_price"]):
            self.cache.save_stock_price(ticker, yr, p)
            
        # Save exchange rates (average and closing)
        for yr, r in zip(years, normalized_data["exchange_rate_to_reporting_currency"]):
            self.cache.save_exchange_rate(
                from_curr=normalized_data["market_currency"],
                to_curr=normalized_data["currency"],
                year=yr,
                rate=r
            )

        if "closing_exchange_rate_to_reporting_currency" in normalized_data:
            for yr, r in zip(years, normalized_data["closing_exchange_rate_to_reporting_currency"]):
                self.cache.save_closing_exchange_rate(
                    from_curr=normalized_data["market_currency"],
                    to_curr=normalized_data["currency"],
                    year=yr,
                    rate=r
                )
            
        # Save fully parsed input JSON document
        self.cache.save_audit_input(ticker, provider_name, normalized_data)

        return validated_input
