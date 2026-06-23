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

    # 1. Precalculate stage discount multipliers once
    m1 = sum(((1 + growth_stage_1) / (1 + wacc)) ** i for i in range(1, stage_1_years + 1))

    base_g1 = (1 + growth_stage_1) ** stage_1_years
    m2 = sum(
        base_g1 * ((1 + growth_stage_2) ** j) / ((1 + wacc) ** (stage_1_years + j))
        for j in range(1, stage_2_years + 1)
    )

    base_g2 = base_g1 * ((1 + growth_stage_2) ** stage_2_years)
    m_tv = (base_g2 * (1 + terminal_growth) / (wacc - terminal_growth)) / ((1 + wacc) ** (stage_1_years + stage_2_years))

    total_multiplier = m1 + m2 + m_tv

    # 2. Vectorized pandas operations
    shares = df["shares_outstanding"] / 1e6 if amount_unit == "million" else df["shares_outstanding"]
    valid_mask = (df["Owner_Earnings"] > 0) & (shares > 0)

    # 3. Compute intrinsic value for valid rows only to avoid division by zero warnings
    intrinsic_value = pd.Series(np.nan, index=df.index, dtype=float)
    if valid_mask.any():
        intrinsic_value[valid_mask] = (df.loc[valid_mask, "Owner_Earnings"] * total_multiplier) / shares[valid_mask]

    return intrinsic_value.rename("Intrinsic_Value_Share")
