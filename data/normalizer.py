import numpy as np
from typing import Dict, Any, List

def normalize_audit_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans, normalizes and completes financial dataset before pydantic validation.
    
    Tasks:
    1. Ensures cash flows are non-negative (reverses negative cash outflows).
    2. Clips tax rates within [0.0, 1.0].
    3. Guarantees shares_outstanding and stock prices are strictly positive (> 0.0).
    4. Handles division-by-zero or nan artifacts.
    """
    data = raw_data.copy()
    financials = data["financials"].copy()
    num_years = len(data["years"])

    # 1. Reverse negative cash flow outflows
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
    for field in non_negative_fields:
        if field in financials:
            # Map values to positive floats
            financials[field] = [abs(float(v)) if v is not None else 0.0 for v in financials[field]]
        else:
            financials[field] = [0.0] * num_years

    # 2. Normalize and check Tax Rates
    if "tax_rate" in financials:
        financials["tax_rate"] = [
            max(0.0, min(1.0, float(v))) if (v is not None and not np.isnan(v)) else 0.18
            for v in financials["tax_rate"]
        ]
    else:
        financials["tax_rate"] = [0.18] * num_years

    # 3. Handle strict positive bounds
    if "shares_outstanding" in financials:
        financials["shares_outstanding"] = [
            float(v) if (v is not None and v > 0) else (100.0 * 1e6 if data["amount_unit"] == "million" else 100.0)
            for v in financials["shares_outstanding"]
        ]
    else:
        financials["shares_outstanding"] = [100.0 * 1e6] * num_years

    if "avg_stock_price" in financials:
        financials["avg_stock_price"] = [
            float(v) if (v is not None and v > 0) else 10.0
            for v in financials["avg_stock_price"]
        ]
    else:
        financials["avg_stock_price"] = [10.0] * num_years

    # 4. Fill key net_profit or ebit lists
    for key in ["net_profit", "ebit"]:
        if key in financials:
            financials[key] = [float(v) if v is not None else 0.0 for v in financials[key]]
        else:
            financials[key] = [0.0] * num_years

    # Align buybacks shares to follow buybacks paid strictly
    for i in range(num_years):
        paid = financials["buybacks_paid"][i]
        shares = financials["buybacks_shares"][i]
        price = financials["avg_stock_price"][i]
        rate = data["exchange_rate_to_reporting_currency"][i]
        price_rep = price * rate

        if paid > 0 and shares <= 0:
            if price_rep > 0:
                financials["buybacks_shares"][i] = paid / price_rep
            else:
                financials["buybacks_shares"][i] = 1e6 # Minimal fallback (1 million shares)
        elif shares > 0 and paid <= 0:
            if price_rep > 0:
                financials["buybacks_paid"][i] = shares * price_rep
            else:
                # Force both to 0 if we can't align
                financials["buybacks_shares"][i] = 0.0
                financials["buybacks_paid"][i] = 0.0

    data["financials"] = financials
    return data
