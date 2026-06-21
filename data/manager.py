from typing import List, Dict, Any, Optional
from models.input_schema import CompanyAuditInput
from data.cache import DatabaseCache
from data.normalizer import normalize_audit_data
from data.providers.yahoo import YahooFinanceProvider
from data.providers.futu import FutuOpenDProvider

class DataManager:
    def __init__(self, db_cache: Optional[DatabaseCache] = None):
        self.cache = db_cache or DatabaseCache()

    def get_audit_input(self, ticker: str, provider_name: str, years: List[int], refresh: bool = False) -> CompanyAuditInput:
        """
        Retrieves the CompanyAuditInput from the cache or pulls it from the specified provider API.
        
        :param ticker: Stock ticker/symbol (e.g. '0700.HK')
        :param provider_name: Provider name ('yahoo' or 'futu')
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
                    return CompanyAuditInput(**cached_dict)

        # 2. Instantiate correct API provider
        if provider_name == "yahoo":
            provider = YahooFinanceProvider()
        elif provider_name == "futu":
            provider = FutuOpenDProvider()
        else:
            raise ValueError(f"Unknown data provider: '{provider_name}'. Supported providers: 'yahoo', 'futu'")

        # 3. Pull raw data from API
        raw_data = provider.fetch_financial_data(ticker, years)

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
            
        # Save exchange rates
        for yr, r in zip(years, normalized_data["exchange_rate_to_reporting_currency"]):
            self.cache.save_exchange_rate(
                from_curr=normalized_data["market_currency"],
                to_curr=normalized_data["currency"],
                year=yr,
                rate=r
            )
            
        # Save fully parsed input JSON document
        self.cache.save_audit_input(ticker, provider_name, normalized_data)

        return validated_input
