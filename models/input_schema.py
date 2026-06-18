from pydantic import BaseModel, Field, model_validator
from typing import List

class FinancialsSchema(BaseModel):
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
    buybacks_paid: List[float] = Field(..., description="Cash paid for stock repurchases")
    buybacks_shares_m: List[float] = Field(..., description="Number of shares repurchased in millions")
    ma_paid: List[float] = Field(..., description="Cash paid for acquisitions / M&A")
    goodwill: List[float] = Field(..., description="Goodwill on balance sheet")
    shares_outstanding_m: List[float] = Field(..., description="Number of shares outstanding in millions")
    avg_stock_price: List[float] = Field(..., description="Average annual stock price")

class CompanyAuditInput(BaseModel):
    ticker: str
    company_name: str
    currency: str
    years: List[int]
    financials: FinancialsSchema

    @model_validator(mode="after")
    def validate_lengths(self) -> "CompanyAuditInput":
        num_years = len(self.years)
        for name, field_value in self.financials.__dict__.items():
            if isinstance(field_value, list):
                if len(field_value) != num_years:
                    raise ValueError(
                        f"Field '{name}' in financials must have length {num_years} to match 'years', but got length {len(field_value)}"
                    )
        return self
