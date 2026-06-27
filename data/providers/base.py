from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseProvider(ABC):
    @abstractmethod
    def fetch_financial_data(self, ticker: str, years: List[int]) -> Dict[str, Any]:
        """
        Fetches raw financials, stock prices, and exchange rates for the given ticker and years.
        
        :param ticker: Stock ticker/symbol (e.g., '0388.HK').
        :param years: List of integer fiscal years.
        :return: A dictionary containing metadata, financials, stock prices, and exchange rates.
        """
        pass
