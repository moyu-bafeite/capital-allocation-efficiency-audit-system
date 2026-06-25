from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


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
    title: str,
    status: str,
    value: Any,
    benchmark: Any,
    description: str,
) -> Dict[str, Any]:
    return {
        "index": index,
        "title": title,
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
            "资本回报率是否高于资本成本？",
            "insufficient_data",
            "N/A",
            f"WACC {wacc:.1%}",
            "ROIC 数据不足，无法判断是否创造价值。",
        )
    else:
        spread = avg_roic - wacc
        if spread > 0:
            status = "pass"
            desc = f"近 5 年平均 ROIC {avg_roic:.1%} 高于 WACC {wacc:.1%}，利差 +{spread:.1%}，公司持续创造经济价值。"
        else:
            status = "fail"
            desc = f"近 5 年平均 ROIC {avg_roic:.1%} 低于 WACC {wacc:.1%}，利差 {spread:.1%}，公司在毁灭股东价值。"
        p1 = _build_principle(
            1,
            "资本回报率是否高于资本成本？",
            status,
            f"{avg_roic:.1%}",
            f"WACC {wacc:.1%}（利差 {spread:+.1%}）",
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
            "留存利润是否被高效再投资？",
            "insufficient_data",
            "N/A",
            f"ROIC {avg_roic:.1%}" if not pd.isna(avg_roic) else "N/A",
            "ROIIC 数据不足，无法评估增量再投资效率。",
        )
    else:
        if np.isinf(latest_roiic):
            status = "pass"
            val_str = "极高 (Capital-Light)"
            desc = (
                f"公司在过去 {roiic_window} 年累计未留下任何盈余（可能全部用于分红与回购），"
                f"但税后经营利润 (NOPAT) 仍然实现了增长。这代表了极其优异的**“零资本 / 轻资产扩张模式”**，"
                f"边际增量再投资效率极高！"
            )
        elif latest_roiic >= avg_roic:
            status = "pass"
            val_str = f"{latest_roiic:.1%}"
            desc = (
                f"ROIIC {latest_roiic:.1%} ≥ ROIC {avg_roic:.1%}，"
                f"增量投资回报不低于存量资本，管理层仍能找到高回报投资机会。"
            )
        elif latest_roiic >= wacc:
            status = "warning"
            val_str = f"{latest_roiic:.1%}"
            desc = (
                f"ROIIC {latest_roiic:.1%} < ROIC {avg_roic:.1%}，边际效率递减，"
                f"但仍高于 WACC {wacc:.1%}，再投资仍在创造价值但护城河可能收窄。"
            )
        else:
            status = "fail"
            val_str = f"{latest_roiic:.1%}"
            desc = (
                f"ROIIC {latest_roiic:.1%} < WACC {wacc:.1%}，"
                f"增量投资回报低于资本成本，管理层在低效扩张，应转向分红或回购。"
            )
        p2 = _build_principle(
            2,
            "留存利润是否被高效再投资？",
            status,
            val_str,
            f"ROIC {avg_roic:.1%}",
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
            "每 $1 留存是否创造 >$1 市值？",
            "insufficient_data",
            "N/A",
            "$1.00 / $1",
            "一美元原则数据不足，无法评估市值创造效率。",
        )
    else:
        if latest_one_dollar >= 1.0:
            status = "pass"
            desc = (
                f"每留存 $1 创造了 ${latest_one_dollar:.2f} 市值，"
                f"市场对管理层的资本配置投出信任票。"
            )
        elif latest_one_dollar >= 0.5:
            status = "warning"
            desc = (
                f"每留存 $1 仅创造 ${latest_one_dollar:.2f} 市值，"
                f"留存利润的市场认可度不足，资本配置效率存疑。"
            )
        else:
            status = "fail"
            desc = (
                f"每留存 $1 仅创造 ${latest_one_dollar:.2f} 市值，"
                f"管理层截留利润却未能转化为市场价值，严重摧毁股东财富。"
            )
        p3 = _build_principle(
            3,
            "每 $1 留存是否创造 >$1 市值？",
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
            "回购是否具有纪律性（低于内在价值）？",
            "insufficient_data",
            "N/A",
            "≤ 0.85x 内在价值",
            "审计期间无显著回购记录，无法评估回购纪律。",
        )
    else:
        buyback_weights = df.loc[buyback_ratios.index, "buybacks_paid"].clip(lower=0)
        if buyback_weights.sum() > 0:
            avg_buyback_ratio = float(np.average(buyback_ratios, weights=buyback_weights))
        else:
            avg_buyback_ratio = float(buyback_ratios.mean())

        if avg_buyback_ratio <= 0.85:
            status = "pass"
            desc = (
                f"加权回购均价为内在价值的 {avg_buyback_ratio:.2f}x，"
                f"管理层在低估时回购，实实在在地增厚长期股东权益。"
            )
        elif avg_buyback_ratio <= 1.10:
            status = "warning"
            desc = (
                f"加权回购均价为内在价值的 {avg_buyback_ratio:.2f}x，"
                f"回购价格接近公允价值，未造成重大价值损失但也未创造显著超额回报。"
            )
        else:
            status = "fail"
            desc = (
                f"加权回购均价为内在价值的 {avg_buyback_ratio:.2f}x，"
                f"管理层在高估时回购，用真金白银补贴离场股东，损害长期持有者利益。"
            )
        p4 = _build_principle(
            4,
            "回购是否具有纪律性（低于内在价值）？",
            status,
            f"{avg_buyback_ratio:.2f}x 内在价值",
            "≤ 0.85x",
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
            "分红是否被自由现金流覆盖？",
            "insufficient_data",
            "N/A",
            "FCF 派发率 ≤ 100%",
            "审计期间未进行现金分红或回购，无法评估分红可持续性。",
        )
    elif total_fcf <= 0:
        fcf_payout_ratio = np.nan
        p5 = _build_principle(
            5,
            "分红是否被自由现金流覆盖？",
            "fail",
            "N/A（FCF 为负）",
            "FCF 派发率 ≤ 100%",
            f"累计自由现金流为负，公司在举债分红或回购，不可持续。",
        )
    else:
        fcf_payout_ratio = total_payout / total_fcf
        if fcf_payout_ratio <= 1.0:
            status = "pass"
            desc = (
                f"FCF 派发率 {fcf_payout_ratio:.1%}，"
                f"分红与回购完全被自由现金流覆盖，可持续。"
            )
        elif fcf_payout_ratio <= 1.25:
            status = "warning"
            desc = (
                f"FCF 派发率 {fcf_payout_ratio:.1%}，"
                f"分红略超自由现金流，长期可能需举债维持，需关注。"
            )
        else:
            status = "fail"
            desc = (
                f"FCF 派发率 {fcf_payout_ratio:.1%}，"
                f"分红大幅超出自由现金流，不可持续，存在毁灭价值风险。"
            )
        p5 = _build_principle(
            5,
            "分红是否被自由现金流覆盖？",
            status,
            f"{fcf_payout_ratio:.1%}",
            "≤ 100%",
            desc,
        )

    principles.append(p5)

    # ---- Principle 6: Is capital efficiency trending in the right direction? ----
    if len(recent_roic) >= 2:
        first_roic = float(recent_roic.iloc[0])
        last_roic = float(recent_roic.iloc[-1])
        trend = last_roic - first_roic

        if pd.isna(first_roic) or pd.isna(last_roic):
            p6 = _build_principle(
                6,
                "资本效率趋势是否改善？",
                "insufficient_data",
                "N/A",
                "ROIC 趋势",
                "ROIC 数据不足，无法判断趋势方向。",
            )
        elif trend > 0.01:
            status = "pass"
            desc = (
                f"近 {len(recent_roic)} 年 ROIC 从 {first_roic:.1%} "
                f"提升至 {last_roic:.1%}（+{trend:.1%}），护城河持续加固。"
            )
        elif trend > -0.03:
            status = "warning"
            desc = (
                f"近 {len(recent_roic)} 年 ROIC 从 {first_roic:.1%} "
                f"变动至 {last_roic:.1%}（{trend:+.1%}），基本稳定但需关注。"
            )
        else:
            status = "fail"
            desc = (
                f"近 {len(recent_roic)} 年 ROIC 从 {first_roic:.1%} "
                f"下滑至 {last_roic:.1%}（{trend:.1%}），护城河明显侵蚀。"
            )
        p6 = _build_principle(
            6,
            "资本效率趋势是否改善？",
            status,
            f"{first_roic:.1%} → {last_roic:.1%}",
            f"趋势 {trend:+.1%}",
            desc,
        )
    else:
        p6 = _build_principle(
            6,
            "资本效率趋势是否改善？",
            "insufficient_data",
            "N/A",
            "ROIC 趋势",
            "ROIC 数据点不足（需至少 2 年），无法判断趋势。",
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
        p7 = _build_principle(
            7,
            "并购是否创造高于资本成本的价值？",
            "insufficient_data",
            "N/A",
            f"ROIC {avg_roic:.1%} / WACC {wacc:.1%}" if not pd.isna(avg_roic) else "N/A",
            "审计期间无显著并购支出，或 Acquisition ROIIC 数据不足，无法评估并购资本效率。",
        )
    else:
        if latest_acquisition_roiic >= avg_roic:
            status = "pass"
            desc = (
                f"Acquisition ROIIC {latest_acquisition_roiic:.1%} ≥ ROIC {avg_roic:.1%}，"
                f"并购支出带来的增量回报不低于存量资本，管理层在为股东创造价值。"
            )
        elif latest_acquisition_roiic >= wacc:
            status = "warning"
            desc = (
                f"Acquisition ROIIC {latest_acquisition_roiic:.1%} < ROIC {avg_roic:.1%}，"
                f"并购回报边际递减但仍高于 WACC {wacc:.1%}，并购尚在创造价值但溢价纪律需警惕。"
            )
        else:
            status = "fail"
            desc = (
                f"Acquisition ROIIC {latest_acquisition_roiic:.1%} < WACC {wacc:.1%}，"
                f"并购支出回报低于资本成本，管理层疑似正在毁灭股东价值。"
            )
        p7 = _build_principle(
            7,
            "并购是否创造高于资本成本的价值？",
            status,
            f"{latest_acquisition_roiic:.1%}",
            f"ROIC {avg_roic:.1%} / WACC {wacc:.1%}",
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
            "盈利质量是否健康（现金转化）？",
            "insufficient_data",
            "N/A",
            "FCF / 净利润 ≥ 80%",
            "审计期间无正净利润年度，无法评估盈利的现金支撑度。",
        )
    else:
        fcf_aligned = ocf_aligned.loc[positive_np.index] - capex_aligned.loc[positive_np.index]
        ratios = fcf_aligned / positive_np
        avg_fcf_to_ni = float(ratios.mean())

        if avg_fcf_to_ni >= 0.8:
            status = "pass"
            desc = (
                f"近 {len(ratios)} 年平均 FCF/净利润 {avg_fcf_to_ni:.1%}，"
                f"盈利高度由自由现金流支撑，会计利润含金量充足。"
            )
        elif avg_fcf_to_ni >= 0.5:
            status = "warning"
            desc = (
                f"近 {len(ratios)} 年平均 FCF/净利润 {avg_fcf_to_ni:.1%}，"
                f"现金转化偏低，应计项偏重，盈利质量需结合应收与存货进一步核查。"
            )
        else:
            status = "fail"
            desc = (
                f"近 {len(ratios)} 年平均 FCF/净利润 {avg_fcf_to_ni:.1%}，"
                f"自由现金流远低于会计利润，盈利高度依赖应计项，质量存疑。"
            )
        p8 = _build_principle(
            8,
            "盈利质量是否健康（现金转化）？",
            status,
            f"{avg_fcf_to_ni:.1%}",
            "≥ 80%",
            desc,
        )

    principles.append(p8)

    # ---- Summary ----
    pass_count = sum(1 for p in principles if p["status"] == "pass")
    warning_count = sum(1 for p in principles if p["status"] == "warning")
    fail_count = sum(1 for p in principles if p["status"] == "fail")
    insufficient_count = sum(1 for p in principles if p["status"] == "insufficient_data")

    summary = f"{pass_count}/{len(principles)} 原则通过"
    if warning_count > 0:
        summary += f"，{warning_count} 条警告"
    if fail_count > 0:
        summary += f"，{fail_count} 条未通过"
    if insufficient_count > 0:
        summary += f"，{insufficient_count} 条数据不足"

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
