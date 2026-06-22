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
    elif avg_roic >= 0.20:
        roic_score = 100.0
    elif avg_roic >= 0.15:
        roic_score = 90.0
    elif avg_roic >= 0.10:
        roic_score = 75.0
    elif avg_roic >= 0.05:
        roic_score = 60.0
    else:
        roic_score = 40.0

    roiic_window, roiic_col, latest_roiic = _latest_longest_window_value(df, "ROIIC_Retained_")
    if pd.isna(latest_roiic):
        roiic_score = 75.0
    elif latest_roiic >= 0.20:
        roiic_score = 100.0
    elif latest_roiic >= 0.15:
        roiic_score = 90.0
    elif latest_roiic >= 0.10:
        roiic_score = 75.0
    elif latest_roiic >= 0.05:
        roiic_score = 60.0
    else:
        roiic_score = 40.0

    one_dollar_window, one_dollar_col, latest_one_dollar = _latest_longest_window_value(
        df, "One_Dollar_Rule_"
    )
    if pd.isna(latest_one_dollar):
        one_dollar_score = 75.0
    elif latest_one_dollar >= 1.5:
        one_dollar_score = 100.0
    elif latest_one_dollar >= 1.0:
        one_dollar_score = 80.0
    elif latest_one_dollar >= 0.5:
        one_dollar_score = 60.0
    else:
        one_dollar_score = 30.0

    buyback_ratios = df["Buyback_to_Intrinsic_Ratio"].dropna()
    if buyback_ratios.empty:
        buyback_score = 80.0
        avg_buyback_ratio = np.nan
    else:
        buyback_weights = df.loc[buyback_ratios.index, "buybacks_paid"].clip(lower=0)
        if buyback_weights.sum() > 0:
            avg_buyback_ratio = np.average(buyback_ratios, weights=buyback_weights)
        else:
            avg_buyback_ratio = buyback_ratios.mean()

        if avg_buyback_ratio <= 0.80:
            buyback_score = 100.0
        elif avg_buyback_ratio <= 1.00:
            buyback_score = 90.0
        elif avg_buyback_ratio <= 1.15:
            buyback_score = 70.0
        elif avg_buyback_ratio <= 1.30:
            buyback_score = 50.0
        else:
            buyback_score = 30.0

    total_payout = df["dividends_paid"].sum() + df["buybacks_paid"].sum()
    total_owner_earnings = df["Owner_Earnings"].sum() if "Owner_Earnings" in df.columns else df["net_profit"].sum()
    total_fcf = (df["operating_cash_flow"] - df["capex"]).sum()
    payout_ratio = total_payout / total_owner_earnings if total_owner_earnings > 0 else 0.0
    fcf_payout_ratio = total_payout / total_fcf if total_fcf > 0 else np.nan

    if avg_roic < 0.08:
        if payout_ratio >= 0.75:
            payout_score = 100.0
        elif payout_ratio >= 0.60:
            payout_score = 80.0
        elif payout_ratio >= 0.40:
            payout_score = 60.0
        elif payout_ratio >= 0.20:
            payout_score = 40.0
        else:
            payout_score = 20.0
    elif payout_ratio >= 0.30:
        payout_score = 100.0
    else:
        payout_score = 85.0

    if total_payout > 0:
        if total_owner_earnings <= 0:
            payout_score = min(payout_score, 40.0)
        elif pd.isna(fcf_payout_ratio):
            payout_score = min(payout_score, 55.0)
        elif fcf_payout_ratio > 1.25:
            payout_score = min(payout_score, 55.0)
        elif fcf_payout_ratio > 1.0:
            payout_score = min(payout_score, 70.0)

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
