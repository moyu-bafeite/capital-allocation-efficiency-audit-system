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
    lease_liability_current: Optional[List[float]] = Field(default=None, description="Current portion of lease liabilities (IFRS 16), non-negative")
    lease_liability_non_current: Optional[List[float]] = Field(default=None, description="Non-current portion of lease liabilities (IFRS 16), non-negative")
    convertible_bonds: Optional[List[float]] = Field(default=None, description="Convertible notes and bonds (interest-bearing), non-negative")
    notes_payable: Optional[List[float]] = Field(default=None, description="Notes payable / short-term paper (interest-bearing), non-negative")
    cash_and_equivalents: List[float] = Field(..., description="Cash and equivalents / liquid investments")
    operating_cash_flow: List[float] = Field(..., description="Net cash flow from operating activities")
    capex: List[float] = Field(..., description="Capital expenditures")
    da: List[float] = Field(..., description="Depreciation and amortization")
    dividends_paid: List[float] = Field(..., description="Dividends paid to shareholders")
    buybacks_paid: List[float] = Field(..., description="Cash paid for stock repurchases, in reporting currency and amount_unit")
    buybacks_shares: List[float] = Field(..., description="Absolute number of shares repurchased")
    ma_paid: List[float] = Field(..., description="Cash paid for acquisitions / M&A (non-negative, normalized from signed API values)")
    goodwill: List[float] = Field(..., description="Goodwill on balance sheet")
    shares_outstanding: List[float] = Field(..., description="Absolute number of outstanding shares (year-end, excl. treasury)")
    avg_stock_price: List[float] = Field(..., description="Average annual stock price, in market_currency per share")
    closing_stock_price: Optional[List[float]] = Field(default=None, description="Closing stock price at the year's last trading day, in market_currency per share. Used for period-end market cap. Falls back to avg_stock_price when absent (e.g. legacy cached data).")
    # Cash-flow-statement non-cash adjustments (used for Owner Earnings). Sourced
    # from the cash flow statement add-back section; sign convention matches the
    # cash flow statement (positive = loss added back to net profit).
    cashflow_impairment_adjustment: Optional[List[float]] = Field(default=None, description="Impairment & provisions add-back from cash flow statement (positive for loss, abs-normalized)")
    cashflow_fair_value_adjustment: Optional[List[float]] = Field(default=None, description="Fair value / revaluation surplus add-back from cash flow statement (positive = gain, negative = loss)")
    # Income-statement items used to normalize NOPAT. Sourced from the income
    # statement (within Operating Profit). Sign: fair value positive = gain;
    # impairment abs-normalized (positive = loss).
    income_impairment_charges: Optional[List[float]] = Field(default=None, description="Impairment & provisions charged in operating profit (income statement, positive for loss, abs-normalized)")
    income_fair_value_changes: Optional[List[float]] = Field(default=None, description="Revaluation surplus / fair value changes included in operating profit (income statement, positive for gain)")
    operating_interest_expense: Optional[List[float]] = Field(default=None, description="Interest expense deducted above operating profit (e.g. CK Asset), added back to restore EBIT. Non-negative")
    share_of_profit_associates: Optional[List[float]] = Field(default=None, description="Share of profits of associates (after tax, below operating profit)")
    share_of_profit_joint_venture: Optional[List[float]] = Field(default=None, description="Share of profit from joint venture companies (after tax, below operating profit)")
    special_items_of_operating_profit: Optional[List[float]] = Field(default=None, description="Special items of operating profit / exceptional operating items")
    special_items_of_net_profit: Optional[List[float]] = Field(default=None, description="Special items of net profit / exceptional non-operating items")
    short_term_deposits: Optional[List[float]] = Field(default=None, description="Short-term deposits")
    time_deposits_current: Optional[List[float]] = Field(default=None, description="Time deposits (current)")
    short_term_investment: Optional[List[float]] = Field(default=None, description="Short-term investments")
    long_term_investment: Optional[List[float]] = Field(default=None, description="Long-term investments")
    fair_value_financial_assets_current: Optional[List[float]] = Field(default=None, description="Fair value of financial assets (current)")
    derivative_financial_assets_current: Optional[List[float]] = Field(default=None, description="Derivative financial assets (current)")
    available_for_sale_financial_assets_current: Optional[List[float]] = Field(default=None, description="Available for sale financial assets (current)")
    available_for_sale_financial_assets_non_current: Optional[List[float]] = Field(default=None, description="Available for sale financial assets (non-current)")
    fair_value_financial_assets_non_current: Optional[List[float]] = Field(default=None, description="Fair value of financial assets (non-current)")
    derivative_financial_assets_non_current: Optional[List[float]] = Field(default=None, description="Derivative financial assets (non-current)")
    time_deposits_non_current: Optional[List[float]] = Field(default=None, description="Time deposits (non-current)")

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
        optional_fields = [
            "lease_liability_current",
            "lease_liability_non_current",
            "convertible_bonds",
            "notes_payable",
            "cashflow_impairment_adjustment",
            "cashflow_fair_value_adjustment",
            "income_impairment_charges",
            "income_fair_value_changes",
            "operating_interest_expense",
            "share_of_profit_associates",
            "share_of_profit_joint_venture",
            "special_items_of_operating_profit",
            "special_items_of_net_profit",
            "short_term_deposits",
            "time_deposits_current",
            "short_term_investment",
            "long_term_investment",
            "fair_value_financial_assets_current",
            "derivative_financial_assets_current",
            "available_for_sale_financial_assets_current",
            "available_for_sale_financial_assets_non_current",
            "fair_value_financial_assets_non_current",
            "derivative_financial_assets_non_current",
            "time_deposits_non_current",
        ]
        for field_name in optional_fields:
            if getattr(self.financials, field_name) is None:
                setattr(self.financials, field_name, [0.0] * num_years)

        # closing_stock_price: fall back to avg_stock_price when absent (legacy
        # cached data without the field). Normalizer also handles this, but the
        # validator is the last line of defense before the data is used.
        if getattr(self.financials, "closing_stock_price", None) is None:
            setattr(self.financials, "closing_stock_price", list(self.financials.avg_stock_price))

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
        if any(price <= 0 for price in self.financials.closing_stock_price):
            raise ValueError("All closing_stock_price values must be greater than 0")

        non_negative_fields = [
            "interest_expense",
            "short_term_debt",
            "long_term_debt",
            "lease_liability_current",
            "lease_liability_non_current",
            "convertible_bonds",
            "notes_payable",
            "cash_and_equivalents",
            "capex",
            "da",
            "dividends_paid",
            "buybacks_paid",
            "buybacks_shares",
            "ma_paid",
            "goodwill",
            "cashflow_impairment_adjustment",
            "income_impairment_charges",
            "operating_interest_expense",
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
