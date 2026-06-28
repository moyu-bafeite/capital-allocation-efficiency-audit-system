from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from core.buyback_audit import audit_buybacks
from core.calculator import FinancialCalculator
from core.checklist import generate_checklist
from core.valuation import calculate_intrinsic_value
from models.input_schema import CompanyAuditInput


@dataclass(frozen=True)
class AuditParams:
    maintenance_capex_ratio: float = 0.5
    roiic_window_1: int = 3
    roiic_window_2: int = 5
    roiic_retained_lag: int = 1
    wacc: float = 0.08
    growth_stage_1: float = 0.08
    growth_stage_2: float = 0.04
    terminal_growth: float = 0.02
    stage_1_years: int = 5
    stage_2_years: int = 5


@dataclass(frozen=True)
class AuditResult:
    calculator: FinancialCalculator
    processed_df: pd.DataFrame
    audited_df: pd.DataFrame
    checklist: Dict[str, Any]
    roiic_retained_col_1: str
    roiic_retained_col_2: str


def run_audit(data: CompanyAuditInput, params: AuditParams) -> AuditResult:
    """
    Run the full automated capital allocation audit workflow.
    """
    if params.wacc <= params.terminal_growth:
        raise ValueError("WACC must be greater than the terminal growth rate.")

    calculator = FinancialCalculator(data, maintenance_capex_ratio=params.maintenance_capex_ratio)
    processed_df = calculator.get_processed_df(
        roiic_window_1=params.roiic_window_1,
        roiic_window_2=params.roiic_window_2,
        roiic_retained_lag=params.roiic_retained_lag,
    )

    audited_df = processed_df.copy()
    audited_df["Intrinsic_Value_Share"] = calculate_intrinsic_value(
        audited_df,
        wacc=params.wacc,
        growth_stage_1=params.growth_stage_1,
        stage_1_years=params.stage_1_years,
        growth_stage_2=params.growth_stage_2,
        stage_2_years=params.stage_2_years,
        terminal_growth=params.terminal_growth,
        amount_unit=data.amount_unit,
    )
    audited_df = audit_buybacks(audited_df, amount_unit=data.amount_unit)
    checklist = generate_checklist(
        audited_df,
        wacc=params.wacc,
        roiic_col=f"ROIIC_Retained_{params.roiic_window_2}Y",
        one_dollar_col=f"One_Dollar_Rule_{params.roiic_window_2}Y",
    )

    return AuditResult(
        calculator=calculator,
        processed_df=processed_df,
        audited_df=audited_df,
        checklist=checklist,
        roiic_retained_col_1=f"ROIIC_Retained_{params.roiic_window_1}Y",
        roiic_retained_col_2=f"ROIIC_Retained_{params.roiic_window_2}Y",
    )
