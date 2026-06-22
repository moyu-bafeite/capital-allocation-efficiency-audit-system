from typing import Any, Dict

import pandas as pd


def generate_commentary(df: pd.DataFrame, score_dict: Dict[str, Any]) -> str:
    """
    Generate a qualitative Chinese audit report from the quantitative scorecard.
    """
    grade = score_dict["grade"]
    avg_roic_pct = f"{score_dict['avg_roic'] * 100:.1f}%" if not pd.isna(score_dict["avg_roic"]) else "N/A"
    latest_roiic_pct = (
        f"{score_dict['latest_roiic'] * 100:.1f}%" if not pd.isna(score_dict["latest_roiic"]) else "N/A"
    )
    latest_1d = f"{score_dict['latest_one_dollar']:.2f}" if not pd.isna(score_dict["latest_one_dollar"]) else "N/A"
    payout_pct = f"{score_dict['payout_ratio'] * 100:.1f}%"
    fcf_payout_pct = (
        f"{score_dict['fcf_payout_ratio'] * 100:.1f}%"
        if not pd.isna(score_dict["fcf_payout_ratio"])
        else "N/A"
    )
    roiic_period = f"最近 {score_dict['roiic_window']} 年" if score_dict.get("roiic_window") else "最近可用窗口"
    one_dollar_period = (
        f"最近 {score_dict['one_dollar_window']} 年" if score_dict.get("one_dollar_window") else "最近可用窗口"
    )

    commentary = []
    commentary.append(f"##### 🎯 审计成绩单：**{grade}**（综合分：{score_dict['composite_score']}/100）")
    commentary.append("**核心财务特征概览**：")
    commentary.append(f"- 最近 5 年投入资本回报率 (ROIC)：**{avg_roic_pct}**")
    commentary.append(f"- {roiic_period}累计留存盈余再投资回报率 (ROIIC)：**{latest_roiic_pct}**")
    commentary.append(f"- {one_dollar_period}“一美元原则”系数：**{latest_1d}**")
    commentary.append(f"- 累计所有者盈余用于“分红 / 回购”比例 (Payout Ratio)：**{payout_pct}**")
    commentary.append(f"- 累计自由现金流用于“分红 / 回购”比例 (FCF Payout Ratio)：**{fcf_payout_pct}**\n")

    commentary.append("###### 1. 存量资产创利能力 (ROIC)")
    if score_dict["roic_score"] >= 90:
        commentary.append(f"该公司的平均 ROIC 高达 {avg_roic_pct}，属于巴菲特极其钟爱的“高经济护城河”企业。公司即使在存量竞争或宏观环境波动下，依然能够凭借极强的议价权、品牌或网络效应维持超高水平的回报率。")
    elif score_dict["roic_score"] >= 75:
        commentary.append(f"该公司的平均 ROIC 处于中上水平 ({avg_roic_pct})。表明企业具备一定竞争壁垒，能够产生超越资本成本的超额回报，但仍需关注稳定性。")
    else:
        commentary.append(f"该公司的平均 ROIC 较低 ({avg_roic_pct})，可能低于其资本成本。若管理层继续大量留存利润再投资，存在蚕食股东财富的风险。")

    commentary.append("###### 2. 增量资本利用效率 (ROIIC)")
    if score_dict["roiic_score"] >= 90:
        commentary.append(f"{roiic_period} ROIIC 高达 {latest_roiic_pct}，说明管理层不仅守业成功，也能把留存盈余投入高回报新项目，展现出优秀的资本配置能力。")
    elif score_dict["roiic_score"] >= 75:
        commentary.append(f"{roiic_period} ROIIC 为 {latest_roiic_pct}，表现合格。公司能较有效地部署留存利润，但需关注增量机会是否随规模扩大而下降。")
    else:
        commentary.append(f"增量再投资回报率 ROIIC 仅为 {latest_roiic_pct}，显示公司可能陷入“规模陷阱”，新增投资回报不足，管理层应提高分红或回购权重。")

    commentary.append("###### 3. 市场价值创造（一美元原则）")
    if score_dict["one_dollar_score"] >= 80:
        commentary.append(f"一美元原则系数为 {latest_1d}。这说明管理层留存的每一元盈余，整体上已转化为较强的市场价值增量。")
    else:
        commentary.append(f"一美元原则系数为 {latest_1d}。这提示管理层留存资金的市场价值转化效率不足，可能存在资本配置失效或留存项目不被市场认可的问题。")

    commentary.append("###### 4. 特殊资本决策（回购与派息时点）")
    buyback_years = df[df["buybacks_paid"] > 0]
    if buyback_years.empty:
        commentary.append("审计期间未发生显著股票回购。若公司 ROIC 极高，不回购可以接受；若估值较低且增量回报下降，则可能错失增厚每股价值的机会。")
    else:
        excellent_buybacks = buyback_years[buyback_years["Buyback_Audit_Rating"].str.contains("卓越")]
        blind_buybacks = buyback_years[buyback_years["Buyback_Audit_Rating"].str.contains("盲目")]
        if not excellent_buybacks.empty and blind_buybacks.empty:
            commentary.append("管理层在回购决策上表现出较强纪律性，主要回购发生在股价低于保守内在价值时，有利于长期股东。")
        elif not blind_buybacks.empty and excellent_buybacks.empty:
            commentary.append("管理层回购存在高估值接盘风险，可能用公司现金补贴离场股东，损害长期股东利益。")
        elif not excellent_buybacks.empty and not blind_buybacks.empty:
            commentary.append("管理层回购动作毁誉参半，既有低估时期的有效回购，也存在估值偏高时期的低效回购。")
        else:
            commentary.append("公司的回购价格大体接近公允内在价值，没有明显价值毁灭，但创造的额外复利也有限。")

    commentary.append("##### ⚖️ 审计结论与投资建议")
    if grade in ["A+", "A"]:
        commentary.append("👉 **投资评级：极高推荐度 (High Conviction Buy - From Allocation Perspective)**\n\n该公司拥有强护城河，同时管理层展现出优秀的资本配置纪律。若估值合理，具备长期持有价值。")
    elif grade == "B":
        commentary.append("👉 **投资评级：持有 / 逢低买入 (Strong Hold)**\n\n公司属于较优秀的价值创造者。建议结合当前估值安全边际进行分批配置。")
    elif grade == "C":
        commentary.append("👉 **投资评级：中性 / 谨慎观望 (Hold / Neutral)**\n\n公司资本配置存在一定瑕疵，需要观察管理层是否改善再投资、分红或回购策略。")
    else:
        commentary.append("👉 **投资评级：警惕 / 避坑 (Avoid - Value Destroyer)**\n\n系统审计显示管理层可能以较低效率消耗资本，需谨慎对待该标的。")

    return "\n".join(commentary)
