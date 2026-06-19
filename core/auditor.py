import pandas as pd
import numpy as np
from typing import Dict, Any, List

class ManagementAuditor:
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the auditor with a processed pandas DataFrame from FinancialCalculator.
        """
        self.df = df.copy()

    def calculate_intrinsic_value(
        self,
        wacc: float = 0.08,
        growth_stage_1: float = 0.08,
        stage_1_years: int = 5,
        growth_stage_2: float = 0.04,
        stage_2_years: int = 5,
        terminal_growth: float = 0.02
    ) -> pd.Series:
        """
        Calculates per-share Intrinsic Value for each year based on that year's Owner Earnings,
        using a two-stage DCF model.
        
        V = sum_{i=1..N} [ OE * (1+g)^i / (1+WACC)^i ] + TerminalValue / (1+WACC)^N
        """
        intrinsic_values_per_share = []
        
        for year in self.df.index:
            oe = self.df.loc[year, "Owner_Earnings"]
            shares = self.df.loc[year, "shares_outstanding_m"]
            
            if oe <= 0 or shares <= 0:
                intrinsic_values_per_share.append(np.nan)
                continue

            # Stage 1 + Stage 2 Projection
            discounted_sum = 0.0
            current_oe = oe
            
            # Stage 1: Fast growth
            for _ in range(stage_1_years):
                current_oe *= (1 + growth_stage_1)
                discounted_sum += current_oe / ((1 + wacc) ** (_ + 1))
            
            # Stage 2: Transition growth
            for i in range(stage_2_years):
                current_oe *= (1 + growth_stage_2)
                discounted_sum += current_oe / ((1 + wacc) ** (stage_1_years + i + 1))
            
            # Terminal Value
            terminal_oe = current_oe * (1 + terminal_growth)
            terminal_value = terminal_oe / (wacc - terminal_growth) if wacc > terminal_growth else 0.0
            discounted_terminal = terminal_value / ((1 + wacc) ** (stage_1_years + stage_2_years))
            
            total_intrinsic_val = discounted_sum + discounted_terminal
            intrinsic_values_per_share.append(total_intrinsic_val / shares)
            
        self.df["Intrinsic_Value_Share"] = intrinsic_values_per_share
        return self.df["Intrinsic_Value_Share"]

    def audit_buybacks(self) -> pd.DataFrame:
        """
        Audits buyback timing and efficacy.
        Compares average buyback price per share against the calculated Intrinsic Value per Share.
        """
        if "Intrinsic_Value_Share" not in self.df.columns:
            self.calculate_intrinsic_value()
            
        buyback_shares = self.df["buybacks_shares_m"]
        buyback_paid = self.df["buybacks_paid"]
        
        # Calculate actual average repurchase price
        self.df["Buyback_Price_Share"] = np.where(
            buyback_shares > 0,
            buyback_paid / buyback_shares,
            0.0
        )
        
        # Compare to Intrinsic Value
        # Buyback Price / Intrinsic Value ratio
        self.df["Buyback_to_Intrinsic_Ratio"] = np.where(
            (self.df["Buyback_Price_Share"] > 0) & (self.df["Intrinsic_Value_Share"] > 0),
            self.df["Buyback_Price_Share"] / self.df["Intrinsic_Value_Share"],
            np.nan
        )
        
        # Categorize
        conditions = [
            self.df["Buyback_to_Intrinsic_Ratio"].isna(),
            self.df["Buyback_to_Intrinsic_Ratio"] <= 0.85,
            (self.df["Buyback_to_Intrinsic_Ratio"] > 0.85) & (self.df["Buyback_to_Intrinsic_Ratio"] <= 1.10),
            self.df["Buyback_to_Intrinsic_Ratio"] > 1.10
        ]
        choices = ["无显著回购", "卓越回购 (低吸/创造价值)", "合理回购 (公允对价)", "盲目回购 (高位抬轿/摧毁价值)"]
        
        self.df["Buyback_Audit_Rating"] = np.select(conditions, choices, default="无显著回购")
        return self.df

    def generate_scorecard(self) -> Dict[str, Any]:
        """
        Generates a comprehensive letter grade and breakdown scorecard for management's capital allocation.
        """
        if "Intrinsic_Value_Share" not in self.df.columns:
            self.calculate_intrinsic_value()
        if "Buyback_to_Intrinsic_Ratio" not in self.df.columns:
            self.audit_buybacks()

        # 1. ROIC Score (30% weight)
        avg_roic = self.df["ROIC"].mean()
        if pd.isna(avg_roic):
            roic_score = 80.0  # Safe default if capital is <= 0 (highly asset-light)
        elif avg_roic >= 0.20:
            roic_score = 100.0
        elif avg_roic >= 0.15:
            roic_score = 90.0
        elif avg_roic >= 0.10:
            roic_score = 75.0
        elif avg_roic >= 0.06:
            roic_score = 60.0
        else:
            roic_score = 40.0

        # 2. ROIIC Score (25% weight)
        # We look at the most recent 5-year rolling ROIIC (or latest non-nan available)
        roiic_cols = [c for c in self.df.columns if c.startswith("ROIIC_Retained_")]
        if roiic_cols:
            latest_roiic = self.df[roiic_cols[0]].dropna().iloc[-1] if not self.df[roiic_cols[0]].dropna().empty else np.nan
        else:
            latest_roiic = np.nan
            
        if pd.isna(latest_roiic):
            roiic_score = 75.0
        elif latest_roiic >= 0.18:
            roiic_score = 100.0
        elif latest_roiic >= 0.12:
            roiic_score = 90.0
        elif latest_roiic >= 0.08:
            roiic_score = 75.0
        elif latest_roiic >= 0.04:
            roiic_score = 60.0
        else:
            roiic_score = 35.0

        # 3. One-Dollar Rule Score (20% weight)
        one_dollar_cols = [c for c in self.df.columns if c.startswith("One_Dollar_Rule_")]
        if one_dollar_cols:
            latest_one_dollar = self.df[one_dollar_cols[0]].dropna().iloc[-1] if not self.df[one_dollar_cols[0]].dropna().empty else np.nan
        else:
            latest_one_dollar = np.nan

        if pd.isna(latest_one_dollar):
            one_dollar_score = 75.0
        elif latest_one_dollar >= 1.5:
            one_dollar_score = 100.0
        elif latest_one_dollar >= 1.0:
            one_dollar_score = 85.0
        elif latest_one_dollar >= 0.5:
            one_dollar_score = 60.0
        else:
            one_dollar_score = 30.0

        # 4. Buyback Timing Score (15% weight)
        # Look at average Buyback-to-Intrinsic ratio for years with buybacks
        buyback_ratios = self.df["Buyback_to_Intrinsic_Ratio"].dropna()
        if buyback_ratios.empty:
            # No buybacks. Were they paying dividends?
            # If they didn't do buybacks, but paid generous dividends (or had high ROIC to reinvest), they shouldn't be penalized heavily.
            buyback_score = 80.0  # Neutral
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

        # 5. Shareholder Payout Appropriateness Score (10% weight)
        # If ROIC is low (<8%), they should pay out dividends/buybacks. If ROIC is high, retention is welcomed.
        # Let's assess: payout_ratio = (dividends + buybacks) / net_profit
        total_profit = self.df["net_profit"].sum()
        total_payout = self.df["dividends_paid"].sum() + self.df["buybacks_paid"].sum()
        payout_ratio = total_payout / total_profit if total_profit > 0 else 0.0
        
        if avg_roic < 0.08:
            # Low return, should return cash
            if payout_ratio >= 0.60:
                payout_score = 100.0
            elif payout_ratio >= 0.40:
                payout_score = 80.0
            elif payout_ratio >= 0.20:
                payout_score = 60.0
            else:
                payout_score = 30.0
        else:
            # High return, retention is okay, but some payout is healthy
            if payout_ratio >= 0.30:
                payout_score = 100.0
            else:
                payout_score = 85.0

        # Calculate weighted composite score
        composite_score = (
            roic_score * 0.30 +
            roiic_score * 0.25 +
            one_dollar_score * 0.20 +
            buyback_score * 0.15 +
            payout_score * 0.10
        )

        # Assign letter grade
        if composite_score >= 93:
            grade = "A+"
        elif composite_score >= 88:
            grade = "A"
        elif composite_score >= 82:
            grade = "B"
        elif composite_score >= 75:
            grade = "C"
        elif composite_score >= 65:
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
            "latest_one_dollar": latest_one_dollar,
            "payout_ratio": payout_ratio
        }

    def generate_commentary(self, score_dict: Dict[str, Any]) -> str:
        """
        Generates a rich, highly targeted qualitative analysis report in Chinese based on Warren Buffett's philosophy.
        """
        grade = score_dict["grade"]
        avg_roic_pct = f"{score_dict['avg_roic']*100:.1f}%" if not pd.isna(score_dict["avg_roic"]) else "N/A"
        latest_roiic_pct = f"{score_dict['latest_roiic']*100:.1f}%" if not pd.isna(score_dict["latest_roiic"]) else "N/A"
        latest_1d = f"{score_dict['latest_one_dollar']:.2f}" if not pd.isna(score_dict["latest_one_dollar"]) else "N/A"
        payout_pct = f"{score_dict['payout_ratio']*100:.1f}%"

        commentary = []
        commentary.append(f"##### 🎯 审计成绩单：**{grade}** (综合分：{score_dict['composite_score']}/100)")
        commentary.append(f"**核心财务特征概览**：")
        commentary.append(f"- 历史平均投入资本回报率 (ROIC)：**{avg_roic_pct}**")
        commentary.append(f"- 最新 5 年累计留存盈余再投资回报率 (ROIIC)：**{latest_roiic_pct}**")
        commentary.append(f"- 最近 5 年“一美元原则”系数：**{latest_1d}**")
        commentary.append(f"- 累计净利润用于“股东分红 / 回购”比例 (Payout Ratio)：**{payout_pct}**\n")

        # Analyze ROIC
        commentary.append("###### 1. 存量资产创利能力 (ROIC)")
        if score_dict["roic_score"] >= 90:
            commentary.append(f"该公司的平均 ROIC 高达 {avg_roic_pct}，属于巴菲特极其钟爱的“高经济护城河”企业。公司即使在存量竞争或宏观环境波动下，依然能够凭借极强的议价权、品牌或网络效应维持超高水平的回报率。管理层护城河守护得当，资产质量极佳。")
        elif score_dict["roic_score"] >= 75:
            commentary.append(f"该公司的平均 ROIC 处于中上水平 ({avg_roic_pct})。表明企业具备一定的竞争壁垒，能够产生超越资本成本的超额回报，但在行业激烈竞争或逆周期时，护城河可能受到部分侵蚀，需关注其稳定性。")
        else:
            commentary.append(f"该公司的平均 ROIC 较低 ({avg_roic_pct})，甚至可能低于其加权平均资本成本 (WACC)。这是一面警钟，说明公司本质上属于平庸企业。如果管理层还一味地留存利润进行再投资，就是在蚕食股东的财富。")

        # Analyze ROIIC & Reinvestment
        commentary.append("###### 2. 增量资本利用效率 (ROIIC)")
        if score_dict["roiic_score"] >= 90:
            commentary.append(f"最新一期 ROIIC 高达 {latest_roiic_pct}，极其优秀！这说明管理层不仅守业成功，创业开拓也极其高效。他们把留存下来的每一分盈余都投在了极高回报的新项目上，未发生“资本帝国的盲目扩张 (Diworsification)”，展现了大师级的资本配置水准。")
        elif score_dict["roiic_score"] >= 75:
            commentary.append(f"增量回报率 ROIIC 为 {latest_roiic_pct}，表现合格。公司能将留存利润有效地部署在生产性资产中，并产生不错的新增利润。然而，这与存量 ROIC 相比存在一定差值，可能预示着随着企业规模变大，高回报的投资机会正在逐步减少。")
        else:
            commentary.append(f"增量再投资回报率 ROIIC 仅为 {latest_roiic_pct}，形势严峻。这代表公司面临典型的“规模陷阱”——存量业务虽然赚钱，但新增投资却是在低回报甚至亏损的项目中“打水漂”。管理层应当立即减少资本支出，将利润全额分红或用于回购，而不是盲目留存。")

        # Analyze One-Dollar Rule
        commentary.append("###### 3. 市场价值创造（一美元原则）")
        if score_dict["one_dollar_score"] >= 85:
            commentary.append(f"一美元原则系数为 {latest_1d}（大于 1.0）。说明在资本市场上，管理层留存的每一元留存盈余，都已经成功转化为了超过一元的市场价值增量。这代表市场对管理层长期留存资金的决策投下了强烈的“信任票”。")
        else:
            commentary.append(f"一美元原则系数为 {latest_1d}（小于 1.0）。这是一个经典的危险信号！在过去 5 年里，管理层截留了大量本应属于股东的现金，但公司的市值增长却远落后于留存资金的规模。管理层面临资本配置失效，市值管理能力不足，或者留存项目不被市场认可。")

        # Analyze Buybacks
        commentary.append("###### 4. 特殊资本决策（回购与派息时点）")
        buyback_years = self.df[self.df["buybacks_paid"] > 0]
        if buyback_years.empty:
            commentary.append("在审计期间，该公司未进行显著的股票回购。管理层的分配方向可能侧重于现金分红或留存再投资。如果公司 ROIC 极高，不回购是可以接受的；但若公司估值极低且 ROIC 下滑，未执行回购则可能错失了增厚股东每股价值的黄金机会。")
        else:
            excellent_buybacks = buyback_years[buyback_years["Buyback_Audit_Rating"].str.contains("卓越")]
            blind_buybacks = buyback_years[buyback_years["Buyback_Audit_Rating"].str.contains("盲目")]
            
            if not excellent_buybacks.empty and blind_buybacks.empty:
                commentary.append("管理层在回购决策上表现出了**极高智慧**。主要回购均发生在股价低于每股保守内在价值时（即安全边际充足的“黄金买点”），这种低位注销股份的行为实实在在地增厚了长期持有者的“所有者权益”。")
            elif not blind_buybacks.empty and excellent_buybacks.empty:
                commentary.append("警告：管理层的回购存在明显的“高位接盘”、“市值操纵”嫌疑。他们在股价高企、远超内在价值的泡沫时期执行了大笔回购，这其实是在用真金白银补贴离场股东，却极大地损害了长期留守股东的利益，属于反向资本配置决策。")
            elif not excellent_buybacks.empty and not blind_buybacks.empty:
                commentary.append("管理层的回购动作毁誉参半。既有在行业周期底部、股价低估时的果断出手，也存在在牛市高峰、高估值时为了迎合市场而进行的高位回购。资本配置的纪律性仍有提升空间。")
            else:
                commentary.append("公司的回购价格基本维持在公允内在价值附近，起到了中规中矩的“股本注销”作用。没有造成重大的价值损失，但也没有创造显著的超额复利。")

        # Final advice
        commentary.append("##### ⚖️ 审计结论与投资建议")
        if grade in ["A+", "A"]:
            commentary.append("👉 **投资评级：极高推荐度 (High Conviction Buy - From Allocation Perspective)**\n\n该公司拥有极其罕见的“超级护城河”，同时管理层展现了巴菲特级别的资本配置艺术：**高 ROIC、高 ROIIC、回购精准、市场认可。** 对于这样的公司，估值合理时应坚决重仓买入，并长期持有，让时间与管理层一起为您复利滚雪球。")
        elif grade in ["B"]:
            commentary.append("👉 **投资评级：持有 / 逢低买入 (Strong Hold)**\n\n该公司属于优秀的“价值创造者”。管理层资本配置能力及格偏上。虽然随着规模变大增量效率稍显平庸，但护城河基本盘依然稳固。建议结合当前股价的安全边际（PB/PE/DCF 折扣）进行定投或分批买入。")
        elif grade in ["C"]:
            commentary.append("👉 **投资评级：中性 / 谨慎观望 (Hold / Neutral)**\n\n公司管理层在资本配置上暴露出了一定的问题：可能是新增投资效率极低，亦或是在高估值时期盲目回购、大手笔并购积累商誉。需要密切关注管理层是否会转变为“现金奶牛”开始加大分红。若无明显的分配策略转型，暂不建议重仓。")
        else:
            commentary.append("👉 **投资评级：警惕 / 避坑 (Avoid - Value Destroyer)**\n\n**强烈建议避开该标的！** 即使财报上的名义利润可能好看，但系统的“照妖镜”审计表明，管理层正在以极低的效率耗费社会资本，通过低回报再投资、高价接盘回购或无谓的商誉减值来摧毁股东资产。一美元原则极差，是不折不扣的“价值毁灭者”。")

        return "\n".join(commentary)
