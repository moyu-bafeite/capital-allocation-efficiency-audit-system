from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from i18n import Translatable


def _latest_longest_window_value(
    df: pd.DataFrame, prefix: str
) -> tuple[Optional[int], Optional[str], float]:
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


def _build_principle(
    index: int,
    title_key: str,
    status: str,
    value: Any,
    benchmark: Any,
    description: Translatable,
) -> Dict[str, Any]:
    return {
        "index": index,
        "title_key": title_key,
        "status": status,
        "value": value,
        "benchmark": benchmark,
        "description": description,
    }


def generate_checklist(
    df: pd.DataFrame,
    wacc: float,
    roiic_col: Optional[str] = None,
    one_dollar_col: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a Buffett capital allocation principles checklist.

    Each principle returns factual data and a pass/fail/warning status
    based on objective thresholds, NOT subjective scores.
    """

    principles: List[Dict[str, Any]] = []

    # ---- Principle 1: Is ROIC above cost of capital? ----
    recent_roic = df["ROIC"].tail(5).dropna()
    avg_roic = recent_roic.mean() if not recent_roic.empty else np.nan

    if pd.isna(avg_roic):
        p1 = _build_principle(
            1,
            "checklist.p1.title",
            "insufficient_data",
            "N/A",
            f"WACC {wacc:.1%}",
            Translatable("checklist.p1.desc.insufficient"),
        )
    elif np.isinf(avg_roic) or (avg_roic > 10.0):
        status = "pass"
        p1 = _build_principle(
            1,
            "checklist.p1.title",
            status,
            Translatable("checklist.p1.value.negative_ic"),
            f"WACC {wacc:.1%}",
            Translatable("checklist.p1.desc.money_printer"),
        )
    else:
        spread = avg_roic - wacc
        if spread > 0:
            status = "pass"
            desc = Translatable("checklist.p1.desc.pass", avg_roic=avg_roic, wacc=wacc, spread=spread)
        else:
            status = "fail"
            desc = Translatable("checklist.p1.desc.fail", avg_roic=avg_roic, wacc=wacc, spread=spread)
        p1 = _build_principle(
            1,
            "checklist.p1.title",
            status,
            f"{avg_roic:.1%}",
            Translatable("checklist.p1.benchmark.wacc_spread", wacc=wacc, spread=spread),
            desc,
        )

    principles.append(p1)

    # ---- Principle 2: Is retained profit efficiently reinvested? ----
    roiic_window, resolved_roiic_col, latest_roiic = _latest_longest_window_value(
        df, "ROIIC_Retained_"
    )
    if roiic_col is None:
        roiic_col = resolved_roiic_col

    if pd.isna(latest_roiic) and pd.isna(avg_roic):
        p2 = _build_principle(
            2,
            "checklist.p2.title",
            "insufficient_data",
            "N/A",
            f"ROIC {avg_roic:.1%}" if not pd.isna(avg_roic) else "N/A",
            Translatable("checklist.p2.desc.insufficient"),
        )
    else:
        benchmark_str: Any = (
            Translatable("checklist.p2.benchmark.negative_ic")
            if np.isinf(avg_roic)
            else f"ROIC {avg_roic:.1%}"
        )

        if np.isinf(latest_roiic):
            status = "pass"
            val_str: Any = Translatable("checklist.p2.value.capital_light")
            desc = Translatable("checklist.p2.desc.capital_light", window=roiic_window)
        elif np.isinf(avg_roic):
            if latest_roiic >= wacc:
                status = "pass"
                val_str = f"{latest_roiic:.1%}"
                desc = Translatable("checklist.p2.desc.inf_roic_pass", roiic=latest_roiic, wacc=wacc)
            else:
                status = "fail"
                val_str = f"{latest_roiic:.1%}"
                desc = Translatable("checklist.p2.desc.inf_roic_fail", roiic=latest_roiic, wacc=wacc)
        elif latest_roiic >= avg_roic:
            status = "pass"
            val_str = f"{latest_roiic:.1%}"
            desc = Translatable("checklist.p2.desc.ge_avg", roiic=latest_roiic, roic=avg_roic)
        elif latest_roiic >= wacc:
            status = "warning"
            val_str = f"{latest_roiic:.1%}"
            desc = Translatable("checklist.p2.desc.ge_wacc", roiic=latest_roiic, roic=avg_roic, wacc=wacc)
        else:
            status = "fail"
            val_str = f"{latest_roiic:.1%}"
            desc = Translatable("checklist.p2.desc.lt_wacc", roiic=latest_roiic, wacc=wacc)
        p2 = _build_principle(
            2,
            "checklist.p2.title",
            status,
            val_str,
            benchmark_str,
            desc,
        )

    principles.append(p2)

    # ---- Principle 3: Does every $1 retained create >$1 market value? ----
    one_dollar_window, resolved_one_dollar_col, latest_one_dollar = (
        _latest_longest_window_value(df, "One_Dollar_Rule_")
    )
    if one_dollar_col is None:
        one_dollar_col = resolved_one_dollar_col

    if pd.isna(latest_one_dollar):
        p3 = _build_principle(
            3,
            "checklist.p3.title",
            "insufficient_data",
            "N/A",
            "$1.00 / $1",
            Translatable("checklist.p3.desc.insufficient"),
        )
    else:
        if latest_one_dollar >= 1.0:
            status = "pass"
            desc = Translatable("checklist.p3.desc.pass", value=latest_one_dollar)
        elif latest_one_dollar >= 0.5:
            status = "warning"
            desc = Translatable("checklist.p3.desc.warning", value=latest_one_dollar)
        else:
            status = "fail"
            desc = Translatable("checklist.p3.desc.fail", value=latest_one_dollar)
        p3 = _build_principle(
            3,
            "checklist.p3.title",
            status,
            f"${latest_one_dollar:.2f} / $1",
            "$1.00 / $1",
            desc,
        )

    principles.append(p3)

    # ---- Principle 4: Are buybacks disciplined (below intrinsic Value)? ----
    buyback_ratios = df["Buyback_to_Intrinsic_Ratio"].dropna()
    if buyback_ratios.empty:
        avg_buyback_ratio = np.nan
        p4 = _build_principle(
            4,
            "checklist.p4.title",
            "insufficient_data",
            "N/A",
            Translatable("checklist.p4.benchmark.le_085"),
            Translatable("checklist.p4.desc.insufficient"),
        )
    else:
        buyback_weights = df.loc[buyback_ratios.index, "buybacks_paid"].clip(lower=0)
        if buyback_weights.sum() > 0:
            avg_buyback_ratio = float(np.average(buyback_ratios, weights=buyback_weights))
        else:
            avg_buyback_ratio = float(buyback_ratios.mean())

        if avg_buyback_ratio <= 0.85:
            status = "pass"
            desc = Translatable("checklist.p4.desc.pass", ratio=avg_buyback_ratio)
        elif avg_buyback_ratio <= 1.10:
            status = "warning"
            desc = Translatable("checklist.p4.desc.warning", ratio=avg_buyback_ratio)
        else:
            status = "fail"
            desc = Translatable("checklist.p4.desc.fail", ratio=avg_buyback_ratio)
        p4 = _build_principle(
            4,
            "checklist.p4.title",
            status,
            Translatable("checklist.p4.value.ratio", ratio=avg_buyback_ratio),
            "\u2264 0.85x",
            desc,
        )

    principles.append(p4)

    # ---- Principle 5: Are dividends covered by free cash flow? ----
    total_payout = float(df["dividends_paid"].sum() + df["buybacks_paid"].sum())
    total_fcf = float((df["operating_cash_flow"] - df["capex"]).sum())

    if total_payout <= 0:
        fcf_payout_ratio = np.nan
        p5 = _build_principle(
            5,
            "checklist.p5.title",
            "insufficient_data",
            "N/A",
            Translatable("checklist.p5.benchmark"),
            Translatable("checklist.p5.desc.insufficient"),
        )
    elif total_fcf <= 0:
        fcf_payout_ratio = np.nan
        p5 = _build_principle(
            5,
            "checklist.p5.title",
            "fail",
            Translatable("checklist.p5.value.neg_fcf"),
            Translatable("checklist.p5.benchmark"),
            Translatable("checklist.p5.desc.neg_fcf"),
        )
    else:
        fcf_payout_ratio = total_payout / total_fcf
        if fcf_payout_ratio <= 1.0:
            status = "pass"
            desc = Translatable("checklist.p5.desc.pass", ratio=fcf_payout_ratio)
        elif fcf_payout_ratio <= 1.25:
            status = "warning"
            desc = Translatable("checklist.p5.desc.warning", ratio=fcf_payout_ratio)
        else:
            status = "fail"
            desc = Translatable("checklist.p5.desc.fail", ratio=fcf_payout_ratio)
        p5 = _build_principle(
            5,
            "checklist.p5.title",
            status,
            f"{fcf_payout_ratio:.1%}",
            "\u2264 100%",
            desc,
        )

    principles.append(p5)

    # ---- Principle 6: Is capital efficiency trending in the right direction? ----
    if len(recent_roic) >= 2:
        first_roic = float(recent_roic.iloc[0])
        last_roic = float(recent_roic.iloc[-1])

        if pd.isna(first_roic) or pd.isna(last_roic):
            p6 = _build_principle(
                6,
                "checklist.p6.title",
                "insufficient_data",
                "N/A",
                Translatable("checklist.p6.benchmark.trend"),
                Translatable("checklist.p6.desc.insufficient"),
            )
        elif np.isinf(first_roic) and np.isinf(last_roic):
            status = "pass"
            p6 = _build_principle(
                6,
                "checklist.p6.title",
                status,
                Translatable("checklist.p6.value.sustained_inf"),
                Translatable("checklist.p6.benchmark.excellent"),
                Translatable("checklist.p6.desc.sustained_inf", n_years=len(recent_roic)),
            )
        elif np.isinf(last_roic):
            status = "pass"
            p6 = _build_principle(
                6,
                "checklist.p6.title",
                status,
                Translatable("checklist.p6.value.leap", first_roic=first_roic),
                Translatable("checklist.p6.benchmark.improving"),
                Translatable("checklist.p6.desc.leap", n_years=len(recent_roic), first_roic=first_roic),
            )
        elif np.isinf(first_roic):
            status = "fail"
            p6 = _build_principle(
                6,
                "checklist.p6.title",
                status,
                Translatable("checklist.p6.value.slip", last_roic=last_roic),
                Translatable("checklist.p6.benchmark.advantage"),
                Translatable("checklist.p6.desc.slip", n_years=len(recent_roic), last_roic=last_roic),
            )
        else:
            trend = last_roic - first_roic
            n_years = len(recent_roic)
            if trend > 0.01:
                status = "pass"
                desc = Translatable("checklist.p6.desc.improve", n_years=n_years, first_roic=first_roic, last_roic=last_roic, trend=trend)
            elif trend >= -0.05:
                status = "warning"
                desc = Translatable("checklist.p6.desc.stable", n_years=n_years, first_roic=first_roic, last_roic=last_roic, trend=trend)
            else:
                status = "fail"
                desc = Translatable("checklist.p6.desc.decline", n_years=n_years, first_roic=first_roic, last_roic=last_roic, trend=trend)
            p6 = _build_principle(
                6,
                "checklist.p6.title",
                status,
                f"{first_roic:.1%} \u2192 {last_roic:.1%}",
                Translatable("checklist.p6.benchmark.trend_val", trend=trend),
                desc,
            )
    else:
        p6 = _build_principle(
            6,
            "checklist.p6.title",
            "insufficient_data",
            "N/A",
            Translatable("checklist.p6.benchmark.trend"),
            Translatable("checklist.p6.desc.insufficient_points"),
        )

    principles.append(p6)

    # ---- Principle 7: Do acquisitions create value above cost of capital? ----
    acq_window, resolved_acq_col, latest_acquisition_roiic = _latest_longest_window_value(
        df, "Acquisition_ROIIC_"
    )

    ma_series = df["ma_paid"] if "ma_paid" in df.columns else pd.Series(dtype=float)
    has_ma = bool((ma_series.fillna(0) > 0).any())

    gw_growth_col = next(
        (c for c in df.columns if c.startswith("Goodwill_vs_NOPAT_Growth_")),
        None,
    )
    if gw_growth_col is not None:
        gw_growth_values = df[gw_growth_col].dropna()
        latest_gw_growth = float(gw_growth_values.iloc[-1]) if not gw_growth_values.empty else np.nan
    else:
        latest_gw_growth = np.nan

    if not has_ma or pd.isna(latest_acquisition_roiic):
        if np.isinf(avg_roic):
            benchmark_str: Any = Translatable("checklist.p7.benchmark.inf_roic", wacc=wacc)
        elif not pd.isna(avg_roic):
            benchmark_str = f"ROIC {avg_roic:.1%} / WACC {wacc:.1%}"
        else:
            benchmark_str = "N/A"
        p7 = _build_principle(
            7,
            "checklist.p7.title",
            "insufficient_data",
            "N/A",
            benchmark_str,
            Translatable("checklist.p7.desc.insufficient"),
        )
    else:
        benchmark_str = (
            f"WACC {wacc:.1%}"
            if np.isinf(avg_roic)
            else f"ROIC {avg_roic:.1%} / WACC {wacc:.1%}"
        )

        if np.isinf(latest_acquisition_roiic):
            status = "pass"
            val_str: Any = Translatable("checklist.p7.value.excellent")
            desc = Translatable("checklist.p7.desc.excellent")
        elif np.isinf(avg_roic):
            if latest_acquisition_roiic >= wacc:
                status = "pass"
                val_str = f"{latest_acquisition_roiic:.1%}"
                desc = Translatable("checklist.p7.desc.inf_roic_pass", roiic=latest_acquisition_roiic, wacc=wacc)
            else:
                status = "fail"
                val_str = f"{latest_acquisition_roiic:.1%}"
                desc = Translatable("checklist.p7.desc.inf_roic_fail", roiic=latest_acquisition_roiic, wacc=wacc)
        elif latest_acquisition_roiic >= avg_roic:
            status = "pass"
            val_str = f"{latest_acquisition_roiic:.1%}"
            desc = Translatable("checklist.p7.desc.ge_avg", roiic=latest_acquisition_roiic, roic=avg_roic)
        elif latest_acquisition_roiic >= wacc:
            status = "warning"
            val_str = f"{latest_acquisition_roiic:.1%}"
            desc = Translatable("checklist.p7.desc.ge_wacc", roiic=latest_acquisition_roiic, roic=avg_roic, wacc=wacc)
        else:
            status = "fail"
            val_str = f"{latest_acquisition_roiic:.1%}"
            desc = Translatable("checklist.p7.desc.lt_wacc", roiic=latest_acquisition_roiic, wacc=wacc)
        p7 = _build_principle(
            7,
            "checklist.p7.title",
            status,
            val_str,
            benchmark_str,
            desc,
        )

    principles.append(p7)

    # ---- Principle 8: Is earnings quality healthy (cash-backed)? ----
    np_series = df["net_profit"].tail(5) if "net_profit" in df.columns else pd.Series(dtype=float)
    ocf_series = df["operating_cash_flow"].tail(5) if "operating_cash_flow" in df.columns else pd.Series(dtype=float)
    capex_series = df["capex"].tail(5) if "capex" in df.columns else pd.Series(dtype=float)

    common_idx = np_series.index.intersection(ocf_series.index).intersection(capex_series.index)
    np_aligned = np_series.loc[common_idx]
    ocf_aligned = ocf_series.loc[common_idx]
    capex_aligned = capex_series.loc[common_idx]

    positive_np = np_aligned[np_aligned > 0]

    if positive_np.empty:
        avg_fcf_to_ni = np.nan
        p8 = _build_principle(
            8,
            "checklist.p8.title",
            "insufficient_data",
            "N/A",
            Translatable("checklist.p8.benchmark"),
            Translatable("checklist.p8.desc.insufficient"),
        )
    else:
        fcf_aligned = ocf_aligned.loc[positive_np.index] - capex_aligned.loc[positive_np.index]
        ratios = fcf_aligned / positive_np
        avg_fcf_to_ni = float(ratios.mean())

        n_years = len(ratios)
        if avg_fcf_to_ni >= 0.8:
            status = "pass"
            desc = Translatable("checklist.p8.desc.pass", n_years=n_years, ratio=avg_fcf_to_ni)
        elif avg_fcf_to_ni >= 0.5:
            status = "warning"
            desc = Translatable("checklist.p8.desc.warning", n_years=n_years, ratio=avg_fcf_to_ni)
        else:
            status = "fail"
            desc = Translatable("checklist.p8.desc.fail", n_years=n_years, ratio=avg_fcf_to_ni)
        p8 = _build_principle(
            8,
            "checklist.p8.title",
            status,
            f"{avg_fcf_to_ni:.1%}",
            "\u2265 80%",
            desc,
        )

    principles.append(p8)

    # ---- Summary ----
    pass_count = sum(1 for p in principles if p["status"] == "pass")
    warning_count = sum(1 for p in principles if p["status"] == "warning")
    fail_count = sum(1 for p in principles if p["status"] == "fail")
    insufficient_count = sum(1 for p in principles if p["status"] == "insufficient_data")

    summary = Translatable(
        "checklist.summary",
        pass_count=pass_count,
        total=len(principles),
        warning_count=warning_count,
        fail_count=fail_count,
        insufficient_count=insufficient_count,
    )

    return {
        "principles": principles,
        "pass_count": pass_count,
        "warning_count": warning_count,
        "fail_count": fail_count,
        "insufficient_count": insufficient_count,
        "summary": summary,
        "avg_roic": avg_roic,
        "latest_roiic": latest_roiic,
        "roiic_window": roiic_window,
        "roiic_col": roiic_col,
        "latest_one_dollar": latest_one_dollar,
        "one_dollar_window": one_dollar_window,
        "one_dollar_col": one_dollar_col,
        "avg_buyback_ratio": avg_buyback_ratio,
        "fcf_payout_ratio": fcf_payout_ratio,
        "latest_acquisition_roiic": latest_acquisition_roiic,
        "acquisition_roiic_window": acq_window,
        "acquisition_roiic_col": resolved_acq_col,
        "latest_gw_growth": latest_gw_growth,
        "avg_fcf_to_ni": avg_fcf_to_ni,
    }
