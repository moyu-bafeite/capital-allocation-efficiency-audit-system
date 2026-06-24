from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional

class FinancialsSchema(BaseModel):
    """
    All financial amount fields use reporting currency and amount_unit unless noted otherwise.
    """
    net_profit: List[float] = Field(..., description="Net profit attributable to shareholders")
    ebit: List[float] = Field(..., description="EBIT (Earnings before interest and tax)")
    tax_rate: List[float] = Field(..., description="Effective tax rate (e.g. 0.18)")
    interest_expense: List[float] = Field(..., description="Interest expense on debt")
    total_equity: List[float] = Field(..., description="Total shareholder equity")
    short_term_debt: List[float] = Field(..., description="Short-term interest-bearing debt")
    long_term_debt: List[float] = Field(..., description="Long-term interest-bearing debt")
    cash_and_equivalents: List[float] = Field(..., description="Cash and equivalents / liquid investments")
    operating_cash_flow: List[float] = Field(..., description="Net cash flow from operating activities")
    capex: List[float] = Field(..., description="Capital expenditures")
    da: List[float] = Field(..., description="Depreciation and amortization")
    dividends_paid: List[float] = Field(..., description="Dividends paid to shareholders")
    buybacks_paid: List[float] = Field(..., description="Cash paid for stock repurchases, in reporting currency and amount_unit")
    buybacks_shares: List[float] = Field(..., description="Absolute number of shares repurchased")
    ma_paid: List[float] = Field(..., description="Cash paid for acquisitions / M&A (non-negative, normalized from signed API values)")
    goodwill: List[float] = Field(..., description="Goodwill on balance sheet")
    shares_outstanding: List[float] = Field(..., description="Absolute number of outstanding shares")
    avg_stock_price: List[float] = Field(..., description="Average annual stock price, in market_currency per share")
    impairment_charges: Optional[List[float]] = Field(default=None, description="Goodwill or asset impairment charges (positive for loss)")
    fair_value_changes: Optional[List[float]] = Field(default=None, description="Fair value changes of investment properties or financial assets (positive for gains, negative for losses)")

class CompanyAuditInput(BaseModel):
    ticker: str
    company_name: str
    currency: str = Field(..., description="Reporting currency used by all financial statement amount fields")
    amount_unit: Literal["million", "absolute"] = Field(..., description="Financial amount unit. 'million' or 'absolute'.")
    market_currency: str = Field(..., description="Currency used by avg_stock_price")
    exchange_rate_to_reporting_currency: List[float] = Field(..., description="Annual average exchange rate: market_currency * rate = reporting currency")
    closing_exchange_rate_to_reporting_currency: List[float] = Field(..., description="Closing exchange rate at year-end: market_currency * rate = reporting currency")
    years: List[int]
    financials: FinancialsSchema

    @model_validator(mode="after")
    def validate_lengths(self) -> "CompanyAuditInput":
        num_years = len(self.years)
        
        # Initialize optional financials lists if they are None to maintain backwards-compatibility
        if self.financials.impairment_charges is None:
            self.financials.impairment_charges = [0.0] * num_years
        if self.financials.fair_value_changes is None:
            self.financials.fair_value_changes = [0.0] * num_years

        if num_years < 2:
            raise ValueError("At least two years of financial data are required")
        if any(year <= prev_year for prev_year, year in zip(self.years, self.years[1:])):
            raise ValueError("years must be strictly increasing")
        if not self.ticker.strip() or not self.company_name.strip():
            raise ValueError("ticker and company_name must not be empty")
        if not self.currency.strip() or not self.market_currency.strip():
            raise ValueError("currency and market_currency must not be empty")

        if len(self.exchange_rate_to_reporting_currency) != num_years:
            raise ValueError(
                f"Field 'exchange_rate_to_reporting_currency' must have length {num_years} to match 'years', but got length {len(self.exchange_rate_to_reporting_currency)}"
            )
        if any(rate <= 0 for rate in self.exchange_rate_to_reporting_currency):
            raise ValueError("All average exchange rates must be greater than 0")

        if len(self.closing_exchange_rate_to_reporting_currency) != num_years:
            raise ValueError(
                f"Field 'closing_exchange_rate_to_reporting_currency' must have length {num_years} to match 'years', but got length {len(self.closing_exchange_rate_to_reporting_currency)}"
            )
        if any(rate <= 0 for rate in self.closing_exchange_rate_to_reporting_currency):
            raise ValueError("All closing exchange rates must be greater than 0")

        for name, field_value in self.financials.__dict__.items():
            if isinstance(field_value, list):
                if len(field_value) != num_years:
                    raise ValueError(
                        f"Field '{name}' in financials must have length {num_years} to match 'years', but got length {len(field_value)}"
                    )

        if any(rate < 0 or rate > 1 for rate in self.financials.tax_rate):
            raise ValueError("All tax_rate values must be between 0 and 1")
        if any(shares <= 0 for shares in self.financials.shares_outstanding):
            raise ValueError("All shares_outstanding values must be greater than 0")
        if any(price <= 0 for price in self.financials.avg_stock_price):
            raise ValueError("All avg_stock_price values must be greater than 0")

        non_negative_fields = [
            "interest_expense",
            "short_term_debt",
            "long_term_debt",
            "cash_and_equivalents",
            "capex",
            "da",
            "dividends_paid",
            "buybacks_paid",
            "buybacks_shares",
            "ma_paid",
            "goodwill",
        ]
        for field_name in non_negative_fields:
            values = getattr(self.financials, field_name)
            if any(value < 0 for value in values):
                raise ValueError(f"All {field_name} values must be greater than or equal to 0")

        for year, buybacks_paid, buyback_shares in zip(
            self.years,
            self.financials.buybacks_paid,
            self.financials.buybacks_shares,
        ):
            if buybacks_paid > 0 and buyback_shares <= 0:
                raise ValueError(f"buybacks_shares must be greater than 0 when buybacks_paid is positive in {year}")
            if buyback_shares > 0 and buybacks_paid <= 0:
                raise ValueError(f"buybacks_paid must be greater than 0 when buybacks_shares is positive in {year}")
        return self
