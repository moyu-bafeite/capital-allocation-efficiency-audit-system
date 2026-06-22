from typing import Any, Dict

import pandas as pd

from core.buyback_audit import audit_buybacks
from core.checklist import generate_checklist
from core.valuation import calculate_intrinsic_value


class ManagementAuditor:
    """
    Lightweight orchestrator for the capital allocation audit modules.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def calculate_intrinsic_value(
        self,
        wacc: float = 0.08,
        growth_stage_1: float = 0.08,
        stage_1_years: int = 5,
        growth_stage_2: float = 0.04,
        stage_2_years: int = 5,
        terminal_growth: float = 0.02,
    ) -> pd.Series:
        self.df["Intrinsic_Value_Share"] = calculate_intrinsic_value(
            self.df,
            wacc=wacc,
            growth_stage_1=growth_stage_1,
            stage_1_years=stage_1_years,
            growth_stage_2=growth_stage_2,
            stage_2_years=stage_2_years,
            terminal_growth=terminal_growth,
        )
        return self.df["Intrinsic_Value_Share"]

    def audit_buybacks(self) -> pd.DataFrame:
        if "Intrinsic_Value_Share" not in self.df.columns:
            self.calculate_intrinsic_value()
        self.df = audit_buybacks(self.df)
        return self.df

    def generate_checklist(self, wacc: float = 0.08) -> Dict[str, Any]:
        if "Buyback_to_Intrinsic_Ratio" not in self.df.columns:
            self.audit_buybacks()
        return generate_checklist(self.df, wacc=wacc)
