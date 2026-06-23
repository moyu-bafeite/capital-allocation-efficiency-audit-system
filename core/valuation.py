import numpy as np
import pandas as pd


def calculate_intrinsic_value(
    df: pd.DataFrame,
    wacc: float = 0.08,
    growth_stage_1: float = 0.08,
    stage_1_years: int = 5,
    growth_stage_2: float = 0.04,
    stage_2_years: int = 5,
    terminal_growth: float = 0.02,
    amount_unit: str = "million",
) -> pd.Series:
    """
    Calculate per-share intrinsic value for each year using a two-stage DCF model.
    """
    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than terminal_growth")
    if stage_1_years <= 0 or stage_2_years <= 0:
        raise ValueError("DCF stage years must be greater than 0")

    intrinsic_values_per_share = []

    for year in df.index:
        owner_earnings = df.loc[year, "Owner_Earnings"]
        shares_raw = df.loc[year, "shares_outstanding"]
        shares = shares_raw / 1e6 if amount_unit == "million" else shares_raw

        if owner_earnings <= 0 or shares <= 0:
            intrinsic_values_per_share.append(np.nan)
            continue

        discounted_sum = 0.0
        current_owner_earnings = owner_earnings

        for year_offset in range(stage_1_years):
            current_owner_earnings *= 1 + growth_stage_1
            discounted_sum += current_owner_earnings / ((1 + wacc) ** (year_offset + 1))

        for year_offset in range(stage_2_years):
            current_owner_earnings *= 1 + growth_stage_2
            discount_year = stage_1_years + year_offset + 1
            discounted_sum += current_owner_earnings / ((1 + wacc) ** discount_year)

        terminal_owner_earnings = current_owner_earnings * (1 + terminal_growth)
        terminal_value = terminal_owner_earnings / (wacc - terminal_growth)
        discounted_terminal = terminal_value / ((1 + wacc) ** (stage_1_years + stage_2_years))

        intrinsic_values_per_share.append((discounted_sum + discounted_terminal) / shares)

    return pd.Series(intrinsic_values_per_share, index=df.index, name="Intrinsic_Value_Share")
