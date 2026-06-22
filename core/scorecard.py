from typing import Any, Dict

import numpy as np
import pandas as pd


SCORE_WEIGHTS = {
    "roic": 0.30,
    "roiic": 0.25,
    "one_dollar": 0.20,
    "buyback": 0.10,
    "payout": 0.15,
}


def _latest_longest_window_value(df: pd.DataFrame, prefix: str) -> tuple[int | None, str | None, float]:
    window_cols = []
    for col in [c for c in df.columns if c.startswith(prefix)]:
        window_text = col.replace(prefix, "", 1).removesuffix("Y")
        if window_text.isdigit():
            window_cols.append((int(window_text), col))

    if not window_cols:
        return None, None, np.nan

    window, col = max(window_cols, key=lambda item: item[0])
    values = df[col].dropna()
    latest_value = values.iloc[-1] if not values.empty else np.nan
    return window, col, latest_value


def generate_scorecard(df: pd.DataFrame, custom_weights: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Generate a weighted management capital allocation scorecard.
    """
    weights = custom_weights if custom_weights is not None else SCORE_WEIGHTS
    avg_roic = df["ROIC"].tail(5).mean()
    if pd.isna(avg_roic):
        roic_score = 80.0
    else:
        # ROIC interpolation:
        # <= 0.00 -> 40.0
        #    0.05 -> 60.0
        #    0.10 -> 75.0
        #    0.15 -> 90.0
        # >= 0.20 -> 100.0
        roic_score = np.interp(
            avg_roic,
            [0.00, 0.05, 0.10, 0.15, 0.20],
            [40.0, 60.0, 75.0, 90.0, 100.0]
        )

    roiic_window, roiic_col, latest_roiic = _latest_longest_window_value(df, "ROIIC_Retained_")
    if pd.isna(latest_roiic):
        roiic_score = 75.0
    else:
        # ROIIC interpolation:
        # <= 0.00 -> 40.0
        #    0.05 -> 60.0
        #    0.10 -> 75.0
        #    0.15 -> 90.0
        # >= 0.20 -> 100.0
        roiic_score = np.interp(
            latest_roiic,
            [0.00, 0.05, 0.10, 0.15, 0.20],
            [40.0, 60.0, 75.0, 90.0, 100.0]
        )

    one_dollar_window, one_dollar_col, latest_one_dollar = _latest_longest_window_value(
        df, "One_Dollar_Rule_"
    )
    if pd.isna(latest_one_dollar):
        one_dollar_score = 75.0
    else:
        # One Dollar Rule interpolation:
        # <= 0.00 -> 30.0
        #    0.50 -> 60.0
        #    1.00 -> 80.0
        # >= 1.50 -> 100.0
        one_dollar_score = np.interp(
            latest_one_dollar,
            [0.00, 0.50, 1.00, 1.50],
            [30.0, 60.0, 80.0, 100.0]
        )

    buyback_ratios = df["Buyback_to_Intrinsic_Ratio"].dropna()
    if buyback_ratios.empty:
        # Check if the stock was ever overvalued (stock price > 1.15 * intrinsic value)
        # while they had zero buybacks (virtue of restraint!)
        is_overvalued = False
        if "avg_stock_price_reporting_currency" in df.columns and "Intrinsic_Value_Share" in df.columns:
            overval_mask = (df["avg_stock_price_reporting_currency"] > df["Intrinsic_Value_Share"] * 1.15)
            if overval_mask.any():
                is_overvalued = True
        
        buyback_score = 95.0 if is_overvalued else 80.0
        avg_buyback_ratio = np.nan
    else:
        buyback_weights = df.loc[buyback_ratios.index, "buybacks_paid"].clip(lower=0)
        if buyback_weights.sum() > 0:
            avg_buyback_ratio = np.average(buyback_ratios, weights=buyback_weights)
        else:
            avg_buyback_ratio = buyback_ratios.mean()

        # Continuous linear interpolation for buyback score:
        # ratio <= 0.80 -> 100.0
        # ratio == 1.00 -> 90.0
        # ratio == 1.15 -> 70.0
        # ratio == 1.30 -> 50.0
        # ratio >= 1.50 -> 30.0
        buyback_score = np.interp(
            avg_buyback_ratio,
            [0.80, 1.00, 1.15, 1.30, 1.50],
            [100.0, 90.0, 70.0, 50.0, 30.0]
        )

    total_payout = df["dividends_paid"].sum() + df["buybacks_paid"].sum()
    total_owner_earnings = df["Owner_Earnings"].sum() if "Owner_Earnings" in df.columns else df["net_profit"].sum()
    total_fcf = (df["operating_cash_flow"] - df["capex"]).sum()
    payout_ratio = total_payout / total_owner_earnings if total_owner_earnings > 0 else 0.0
    fcf_payout_ratio = total_payout / total_fcf if total_fcf > 0 else np.nan

    # High-efficiency reinvestment protection:
    # If the company has exceptionally high ROIC (>= 15%) and ROIIC (>= 12%),
    # retaining 100% of profits is the perfect capital allocation choice.
    # Therefore, we excuse low payout ratios and give them 100.0 payout score.
    is_ultra_compounder = (
        (not pd.isna(avg_roic) and avg_roic >= 0.15) and 
        (not pd.isna(latest_roiic) and latest_roiic >= 0.12)
    )

    if is_ultra_compounder:
        payout_score = 100.0
    # Negative earnings protection:
    # If Owner Earnings <= 0, the company has no capacity to pay dividends.
    # - Zero payout is the prudent cash-conservation choice -> 100.0
    # - Forcing payouts while losing money destroys value -> 40.0
    elif total_owner_earnings <= 0:
        payout_score = 100.0 if total_payout == 0 else 40.0
    # Low ROIC companies (< 8%) should return capital to shareholders.
    # Smooth interpolation: 0% -> 20.0, 75%+ -> 100.0
    elif avg_roic < 0.08:
        payout_score = np.interp(
            payout_ratio,
            [0.00, 0.20, 0.40, 0.60, 0.75],
            [20.0, 40.0, 60.0, 80.0, 100.0]
        )
    # Normal / high ROIC companies: moderate payout (>= 30%) is ideal.
    # Smooth interpolation: 0% -> 85.0, 30%+ -> 100.0
    else:
        payout_score = np.interp(
            payout_ratio,
            [0.00, 0.30],
            [85.0, 100.0]
        )

    # Smooth FCF over-allocation penalty (sustainability check):
    if total_payout > 0:
        if total_owner_earnings <= 0:
            payout_score = min(payout_score, 40.0)
        elif pd.isna(fcf_payout_ratio) or total_fcf <= 0:
            # Negative FCF while paying dividends is unsustainable
            payout_score = min(payout_score, 55.0)
        elif fcf_payout_ratio > 1.0:
            # Smooth cap: 1.0 -> 70.0, 1.25 -> 55.0, > 1.25 -> 55.0
            cap_val = np.interp(
                fcf_payout_ratio,
                [1.00, 1.25],
                [70.0, 55.0]
            )
            payout_score = min(payout_score, cap_val)

    composite_score = (
        roic_score * weights["roic"]
        + roiic_score * weights["roiic"]
        + one_dollar_score * weights["one_dollar"]
        + buyback_score * weights["buyback"]
        + payout_score * weights["payout"]
    )

    if composite_score >= 95:
        grade = "A+"
    elif composite_score >= 90:
        grade = "A"
    elif composite_score >= 80:
        grade = "B"
    elif composite_score >= 70:
        grade = "C"
    elif composite_score >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "composite_score": round(composite_score, 1),
        "grade": grade,
        "roic_score": roic_score,
        "roiic_score": roiic_score,
        "one_dollar_score": one_dollar_score,
        "buyback_score": buyback_score,
        "payout_score": payout_score,
        "avg_roic": avg_roic,
        "latest_roiic": latest_roiic,
        "roiic_window": roiic_window,
        "roiic_col": roiic_col,
        "latest_one_dollar": latest_one_dollar,
        "one_dollar_window": one_dollar_window,
        "one_dollar_col": one_dollar_col,
        "payout_ratio": payout_ratio,
        "fcf_payout_ratio": fcf_payout_ratio,
        "avg_buyback_ratio": avg_buyback_ratio,
    }
