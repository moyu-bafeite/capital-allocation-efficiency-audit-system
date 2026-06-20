import numpy as np
import pandas as pd


def audit_buybacks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Audit buyback timing by comparing repurchase price against intrinsic value.
    """
    if "Intrinsic_Value_Share" not in df.columns:
        raise ValueError("Intrinsic_Value_Share is required before auditing buybacks")

    audited_df = df.copy()
    buyback_shares = audited_df["buybacks_shares_m"]
    buyback_paid = audited_df["buybacks_paid"]

    audited_df["Buyback_Price_Share"] = np.where(
        buyback_shares > 0,
        buyback_paid / buyback_shares,
        0.0,
    )

    audited_df["Buyback_to_Intrinsic_Ratio"] = np.where(
        (audited_df["Buyback_Price_Share"] > 0) & (audited_df["Intrinsic_Value_Share"] > 0),
        audited_df["Buyback_Price_Share"] / audited_df["Intrinsic_Value_Share"],
        np.nan,
    )

    conditions = [
        audited_df["Buyback_to_Intrinsic_Ratio"].isna(),
        audited_df["Buyback_to_Intrinsic_Ratio"] <= 0.85,
        (audited_df["Buyback_to_Intrinsic_Ratio"] > 0.85)
        & (audited_df["Buyback_to_Intrinsic_Ratio"] <= 1.10),
        audited_df["Buyback_to_Intrinsic_Ratio"] > 1.10,
    ]
    choices = [
        "无显著回购",
        "卓越回购（低吸 / 创造价值）",
        "合理回购（公允对价）",
        "盲目回购（高位抬轿 / 摧毁价值）",
    ]

    audited_df["Buyback_Audit_Rating"] = np.select(conditions, choices, default="无显著回购")
    return audited_df
