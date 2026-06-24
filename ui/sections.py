import streamlit as st
import numpy as np
import pandas as pd

from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult
from ui.charts import (
    create_allocation_pie_chart,
    create_buyback_chart,
    create_earnings_quality_chart,
    create_ma_goodwill_chart,
    create_roic_chart,
    create_waterfall_chart,
)


SECTION_CAPITAL_ALLOCATION = "**累计资本流向**"
SECTION_ROIC_ROIIC = "**存量与增量回报**"
SECTION_BUYBACK = "**股东回报分配**"
SECTION_MA_GOODWILL = "**并购与商誉审计**"
SECTION_EARNINGS_QUALITY = "**盈利质量审计**"
SECTION_CHECKLIST = "**资本配置清单**"
SECTION_LEDGER = "**原始审计底表**"
SECTIONS = [
    SECTION_CAPITAL_ALLOCATION,
    SECTION_ROIC_ROIIC,
    SECTION_BUYBACK,
    SECTION_MA_GOODWILL,
    SECTION_EARNINGS_QUALITY,
    SECTION_CHECKLIST,
    SECTION_LEDGER,
]


def render_summary(data: CompanyAuditInput, checklist: dict) -> None:
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.metric("标的名称 / 代码", f"{data.company_name} / {data.ticker}")
    with col_meta2:
        st.metric("统计年限", f"{data.years[0]}-{data.years[-1]} ({len(data.years)})")
    with col_meta3:
        display_unit = "元" if data.amount_unit == "absolute" else data.amount_unit
        st.metric("财报币种 / 金额单位", f"{data.currency} / {display_unit}")
    with col_meta4:
        st.metric("市场币种", f"{data.market_currency}")
    st.markdown("---")


def render_navigation() -> str:
    return st.radio(
        "选择审计分析维度 (Audit Dimensions)",
        SECTIONS,
        horizontal=True,
        label_visibility="collapsed"
    )


def render_capital_allocation_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 累计资本流向 (Cumulative Capital Allocation / Sources & Uses)")

    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        time_mode = st.radio(
            "选择时间范围维度 (Select Time Scope)",
            ["任意区间累计分析 (Custom Cumulative Period)", "单一年度专项审计 (Single Fiscal Year Audit)"],
            index=0,
        )

    years = data.years
    start_year = min(years)
    end_year = max(years)
    with col_sel2:
        if time_mode == "任意区间累计分析 (Custom Cumulative Period)":
            selected_years = st.slider(
                "选择时间区间 (Select Year Range)",
                min_value=int(start_year),
                max_value=int(end_year),
                value=(int(start_year), int(end_year)),
                step=1,
            )
            start_year_selected = selected_years[0]
            end_year_selected = selected_years[1]
            st.info(f"当前区间：**{start_year_selected} - {end_year_selected} ({end_year_selected - start_year_selected + 1})**")
        else:
            selected_year = st.selectbox("选择单年度 (Select Fiscal Year)", years, index=len(years) - 1)
            start_year_selected = selected_year
            end_year_selected = selected_year
            st.info(f"当前单年度：**{selected_year}**")

    if start_year_selected == end_year_selected:
        st.markdown(f"追踪 **{start_year_selected}** 单一年度公司通过**经营活动赚取的现金流**，审计管理层如何在**资本支出、现金分红、回购股份、投资并购**等渠道间分配资本。")
    else:
        st.markdown(f"追踪 **{start_year_selected}-{end_year_selected}** 年累计期间公司通过**经营活动赚取的累计现金流**，审计管理层如何在**资本支出、现金分红、回购股份、投资并购**等渠道间分配资本。")

    waterfall_data = result.calculator.get_waterfall_data(start_year_selected, end_year_selected)
    st.plotly_chart(create_waterfall_chart(waterfall_data, start_year_selected, end_year_selected), use_container_width=True)
    st.markdown("###### 资本流向构成比率")
    st.plotly_chart(create_allocation_pie_chart(waterfall_data), use_container_width=True)

    st.markdown("###### 资本分配率诊断")
    c1, c2, c3, c4 = st.columns(4)
    total_ocf = waterfall_data["Total_Operating_Cash_Flow"]

    def _pct(value: float, base: float) -> str:
        return f"{(value / base) * 100:.1f}%" if base > 0 else "N/A"

    with c1:
        st.metric("CapEx 占 OCF 比例", _pct(waterfall_data['CapEx'], total_ocf), help="企业重资产程度。该比例越低，说明企业创造自由现金流的能力越强。")
    with c2:
        st.metric("现金分红率", _pct(waterfall_data['Dividends'], total_ocf), help="分配给股东的现金比例。")
    with c3:
        st.metric("股份回购率", _pct(waterfall_data['Buybacks'], total_ocf), help="利用多余现金在公开市场回购股份注销的力度。")
    with c4:
        st.metric("并购与投资比率", _pct(waterfall_data['M_and_A'], total_ocf), help="管理层通过投资或并购实现增长的力度。若该数值过高但 ROIIC 极低，可能是盲目扩张信号。")


def render_roic_roiic_section(params: AuditParams, result: AuditResult) -> None:
    st.markdown("#### 存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)")
    st.markdown(
        """
        巴菲特强调：投资人不仅要看当前的存量资本回报率 (ROIC)，更要看管理层“截留利润进行再投资”时的增量回报率 (ROIIC)。
        *   **ROIC（存量回报率）**：衡量目前公司已投入资本的运营效率。
        *   **ROIIC Retained（留存再投资回报率）**：$\\Delta NOPAT / 累计留存盈余$。衡量管理层扣留盈利后，再投资的效率。
        """
    )
    st.plotly_chart(
        create_roic_chart(
            result.audited_df,
            result.roiic_retained_col_1,
            result.roiic_retained_col_2,
            params.roiic_window_1,
            params.roiic_window_2,
            params.roiic_retained_lag,
        ),
        use_container_width=True,
    )
    st.info(
        """
        **指引**：
        1. 若 **ROIC 长期维持在 15% 以上**，表明公司产品或服务具备较强护城河。
        2. 若 **ROIIC 大幅低于 ROIC**，表明高回报的新投资机会可能正在减少，管理层应更多考虑分红与回购。
        """
    )


def render_buyback_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 股份回购与红利分配 (Share Repurchase & Dividend Efficacy)")
    st.markdown("本模块对比**实际回购成交均价**和**保守每股内在价值 (DCF)**，甄别管理层是在低估时回购创造复利，还是在高估时回购毁灭价值。")

    display_df = result.audited_df.copy()
    fx_rate = display_df["exchange_rate_to_reporting_currency"]
    display_df["Intrinsic_Value_Share_Market_Currency"] = display_df["Intrinsic_Value_Share"] / fx_rate
    display_df["Buyback_Price_Share_Market_Currency"] = display_df["Buyback_Price_Share"] / fx_rate
    display_df["dividends_paid_market_currency"] = display_df["dividends_paid"] / fx_rate
    display_df["buybacks_paid_market_currency"] = display_df["buybacks_paid"] / fx_rate

    st.plotly_chart(create_buyback_chart(display_df, data.market_currency), use_container_width=True)

    st.markdown("###### 历年回购决策审计明细")
    audit_display_df = display_df[
        [
            "dividends_paid_market_currency",
            "buybacks_paid_market_currency",
            "buybacks_shares",
            "Buyback_Price_Share_Market_Currency",
            "Intrinsic_Value_Share_Market_Currency",
            "Buyback_to_Intrinsic_Ratio",
            "Buyback_Audit_Rating",
        ]
    ].copy()

    if data.amount_unit == "absolute":
        audit_display_df["dividends_paid_market_currency"] *= 1e6
        audit_display_df["buybacks_paid_market_currency"] *= 1e6
        audit_display_df["buybacks_shares"] *= 1e6

    audit_display_df.columns = [
        f"现金派息总额 ({data.market_currency})",
        f"回购现金支出 ({data.market_currency})",
        "回购股份数量（股）",
        f"实际回购均价 ({data.market_currency})",
        f"每股估算内在价值 ({data.market_currency})",
        "回购均价 / 内在价值",
        "回购效率审计结论",
    ]

    st.dataframe(
        audit_display_df.style.format(
            {
                f"现金派息总额 ({data.market_currency})": "{:,.0f}",
                f"回购现金支出 ({data.market_currency})": "{:,.0f}",
                "回购股份数量（股）": "{:,.0f}",
                f"实际回购均价 ({data.market_currency})": "{:,.2f}",
                f"每股估算内在价值 ({data.market_currency})": "{:,.2f}",
                "回购均价 / 内在价值": "{:.2%}",
            }
        ).map(
            lambda value: "font-weight: bold; text-decoration: underline; text-underline-offset: 3px;"
            if "卓越" in str(value)
            else "font-style: italic; font-weight: bold; border-bottom: 2px double rgba(128,128,128,0.8);"
            if "盲目" in str(value)
            else "opacity: 0.5; font-style: italic;"
            if "无显著" in str(value)
            else "",
            subset=["回购效率审计结论"],
        ),
        use_container_width=True,
    )


def render_ma_goodwill_section(data: CompanyAuditInput, params: AuditParams, result: AuditResult) -> None:
    st.markdown("#### 并购与商誉资本效率审计 (M&A & Goodwill Capital Efficiency)")
    st.markdown(
        """
        警惕"帝国建造者"：用高溢价并购堆砌规模，却无法让并购支出赚回资本成本。
        *   **商誉 / 股东权益**：攀升意味着资产负债表愈发依赖并购溢价，减值风险积聚。
        *   **Acquisition ROIIC**：$\\Delta NOPAT / 累计并购支出$。衡量并购资本是否赚回资本成本，低于 WACC 即为价值毁灭。
        *   **商誉增速 vs NOPAT 增速**：正值代表商誉膨胀快于利润增厚，并购未转化为真实盈利。
        """
    )

    acq_col_1 = f"Acquisition_ROIIC_{params.roiic_window_1}Y"
    acq_col_2 = f"Acquisition_ROIIC_{params.roiic_window_2}Y"
    st.plotly_chart(
        create_ma_goodwill_chart(
            result.audited_df,
            acq_col_1,
            acq_col_2,
            params.roiic_window_1,
            params.roiic_window_2,
            params.roiic_retained_lag,
        ),
        use_container_width=True,
    )

    display_df = result.audited_df
    goodwill_growth_col = next(
        (c for c in display_df.columns if c.startswith("Goodwill_vs_NOPAT_Growth_")),
        None,
    )

    ma_total = float(display_df["ma_paid"].sum()) if "ma_paid" in display_df.columns else 0.0
    gw_latest = float(display_df["goodwill"].iloc[-1]) if "goodwill" in display_df.columns else 0.0
    gw_equity_latest = float(display_df["Goodwill_to_Equity"].dropna().iloc[-1]) if "Goodwill_to_Equity" in display_df.columns and not display_df["Goodwill_to_Equity"].dropna().empty else np.nan
    acq_latest = float(display_df[acq_col_2].dropna().iloc[-1]) if acq_col_2 in display_df.columns and not display_df[acq_col_2].dropna().empty else np.nan
    gw_growth_latest = float(display_df[goodwill_growth_col].dropna().iloc[-1]) if goodwill_growth_col and not display_df[goodwill_growth_col].dropna().empty else np.nan

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("累计并购现金支出", f"{ma_total:,.0f}", help="审计期间管理层用于并购/投资的累计现金。")
    with c2:
        st.metric("期末商誉余额", f"{gw_latest:,.0f}", help="资产负债表上的商誉余额，占权益比越高减值风险越大。")
    with c3:
        st.metric("商誉 / 股东权益", f"{gw_equity_latest:.1%}" if not pd.isna(gw_equity_latest) else "N/A", help="商誉占股东权益比例。")
    with c4:
        st.metric("Acquisition ROIIC（最新）", f"{acq_latest:.1%}" if not pd.isna(acq_latest) else "N/A", help="并购支出的增量资本回报率，低于 WACC 即价值毁灭。")

    if not pd.isna(gw_growth_latest):
        if gw_growth_latest > 0.05:
            st.warning(
                f"商誉增速显著超过 NOPAT 增速（差值 +{gw_growth_latest:.1%}），"
                f"并购溢价持续堆积但未能等比例转化为经营利润，警惕未来商誉减值。"
            )
        elif gw_growth_latest < -0.05:
            st.success(
                f"NOPAT 增速超过商誉增速（差值 {gw_growth_latest:.1%}），"
                f"并购整合见效，利润增厚快于商誉膨胀。"
            )

    st.info(
        """
        **指引**：
        1. 若 **商誉 / 股东权益 > 50%** 且 **Acquisition ROIIC < WACC**，管理层大概率在用高溢价并购毁灭价值。
        2. 若累计并购支出可观但 NOPAT 增量微弱，应质疑并购战略而非会计处理。
        """
    )


def render_earnings_quality_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 盈利质量与应计项审计 (Earnings Quality & Accruals Audit)")
    st.markdown(
        """
        巴菲特强调"所有者盈余"而非会计利润：真正属于股东的是现金，不是应计项。
        *   **所有者盈余 vs 净利润**：长期低于净利润，说明盈利被维持性资本支出或非现金项侵蚀。
        *   **FCF / 净利润**：现金转化率，低于 80% 需警惕，低于 50% 说明盈利高度依赖应计项。
        *   **应计项比率**：$(净利润 - 经营现金流) / 投入资本$，持续走高是会计激进的红旗信号（Sloan 异常）。
        *   **每股所有者盈余 (OEPS)**：巴菲特真正在意的"每股内在增长"口径。
        """
    )

    st.plotly_chart(
        create_earnings_quality_chart(result.audited_df),
        use_container_width=True,
    )

    display_df = result.audited_df
    recent = display_df.tail(5)

    def _safe_latest(col):
        if col not in display_df.columns:
            return np.nan
        vals = display_df[col].dropna()
        return float(vals.iloc[-1]) if not vals.empty else np.nan

    oe_ratio_latest = _safe_latest("OE_to_NetProfit")
    fcf_ni_latest = _safe_latest("FCF_to_NetIncome")
    accruals_latest = _safe_latest("Accruals_Ratio")
    oeps_latest = _safe_latest("OEPS")

    oe_vals = recent["Owner_Earnings"].dropna() if "Owner_Earnings" in recent.columns else pd.Series(dtype=float)
    np_vals = recent["net_profit"].dropna() if "net_profit" in recent.columns else pd.Series(dtype=float)
    if not oe_vals.empty and not np_vals.empty and len(oe_vals) == len(np_vals) and (np_vals > 0).all():
        oe_cagr = (oe_vals.iloc[-1] / oe_vals.iloc[0]) ** (1 / max(len(oe_vals) - 1, 1)) - 1
    else:
        oe_cagr = np.nan

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("所有者盈余 / 净利润", f"{oe_ratio_latest:.1%}" if not pd.isna(oe_ratio_latest) else "N/A", help="低于 100% 说明所有者盈余不及会计利润，盈利被维持性资本支出或非现金项侵蚀。")
    with c2:
        st.metric("FCF / 净利润", f"{fcf_ni_latest:.1%}" if not pd.isna(fcf_ni_latest) else "N/A", help="现金转化率，越高说明盈利含金量越足。")
    with c3:
        st.metric("应计项比率", f"{accruals_latest:.1%}" if not pd.isna(accruals_latest) else "N/A", help="正值且走高意味着净利润超过经营现金流，会计利润含应计项偏重。")
    with c4:
        st.metric("每股所有者盈余 (OEPS)", f"{oeps_latest:,.2f}" if not pd.isna(oeps_latest) else "N/A", help="巴菲特真正在意的每股内在增长口径。")

    if not pd.isna(oe_cagr):
        st.info(f"近 {len(oe_vals)} 年所有者盈余年复合增速 (OEPS CAGR)：**{oe_cagr:.1%}**。")

    st.info(
        """
        **指引**：
        1. 若 **所有者盈余长期 < 净利润**，需核查资本支出结构与非现金调整项，盈利质量可能被高估。
        2. 若 **应计项比率持续为正且攀升**，结合应收账款与存货周转排查收入确认激进风险。
        """
    )


def render_checklist_section(result: AuditResult) -> None:
    st.markdown("#### 资本配置原则清单 (Capital Allocation Principles Checklist)")
    st.markdown(
        "以下八条原则基于巴菲特式的资本配置检查清单，"
        "每条原则展示**客观事实数据**与**基准对比**，由系统自动计算判定状态。"
        "用户应结合行业特性与公司生命周期阶段，对未通过或警告的原则进行深入研究。"
    )

    checklist = result.checklist
    principles = checklist["principles"]

    status_config = {
        "pass": {"icon": "[ ✔ 通过 ]", "style": "font-weight: 700; color: #4ca66b;"},
        "fail": {"icon": "[ ✘ 未通过 ]", "style": "font-weight: 700; color: #c0463e; text-decoration: underline;"},
        "warning": {"icon": "[ ! 警告 ]", "style": "font-weight: 700; color: #b8860b; border-bottom: 1px dashed rgba(128,128,128,0.6); display: inline-block;"},
        "insufficient_data": {"icon": "[ ? 数据不足 ]", "style": "font-weight: 400; color: #8a8a8a; opacity: 0.6;"},
    }

    for p in principles:
        cfg = status_config.get(p["status"], status_config["insufficient_data"])
        st.markdown(
            f"""
            <div style="background-color: transparent; padding: 1.2rem 0rem; border-radius: 0px; border-bottom: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 0.5rem;">
                <p style="font-size: 1.05rem; margin: 0 0 0.5rem 0; {cfg['style']}">
                    {cfg['icon']} | 原则 {p['index']}：{p['title']}
                </p>
                <p style="font-size: 0.95rem; margin: 0.25rem 0;">
                    <span style="opacity: 0.6;">实际值：</span><strong>{p['value']}</strong>
                    &nbsp;&nbsp;
                    <span style="opacity: 0.6;">基准：</span><strong>{p['benchmark']}</strong>
                </p>
                <p style="font-size: 0.9rem; opacity: 0.8; margin: 0.5rem 0 0 0;">{p['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.info(
        f"**汇总**：{checklist['summary']}。"
        f"本清单提供事实数据和客观判定，不构成投资建议。"
        f"请结合行业基准、竞争格局和管理层历史决策背景进行独立判断。"
    )


def render_ledger_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 审计模型数据底表 (Raw Data & Intermediaries)")
    st.markdown("以下为系统输入参数、核心中间指标以及最终审计指标：")
    numeric_columns = result.audited_df.select_dtypes(include="number").columns
    
    formatters = {}
    for column in numeric_columns:
        is_ratio_or_price = any(
            x in column.lower() 
            for x in ["rate", "ratio", "price", "roic", "roiic", "rule", "value", "percent"]
        )
        if is_ratio_or_price:
            formatters[column] = "{:,.2f}"
        else:
            formatters[column] = "{:,.0f}"

    st.dataframe(result.audited_df.style.format(formatters), use_container_width=True)
    st.download_button(
        label="导出完整审计表格为 CSV (Export to CSV)",
        data=result.audited_df.to_csv().encode("utf-8-sig"),
        file_name=f"capital_allocation_audit_{data.ticker}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("#### 本地 DuckDB 缓存数据库实时诊断 (DuckDB SQL Diagnostics)")
    st.markdown(
        "本系统采用高能进程内 SQL 数据库 **DuckDB** 存储和管理从 API 抓取的数据。"
        "您可以在下方选择常用的诊断 SQL，或者直接编写自定义 SQL，实时检索并审查本地 DuckDB 缓存内容："
    )

    try:
        import duckdb
        from data.cache import DB_PATH
        import os

        if os.path.exists(DB_PATH):
            col_sql1, col_sql2 = st.columns([1, 3])
            with col_sql1:
                sql_template = st.selectbox(
                    "选择常用 SQL 模板",
                    [
                        "查看最新 10 条财务底表数据",
                        "查看缓存的汇率底表数据",
                        "查看缓存的股价底表数据",
                        "查看所有成功缓存过的股票输入记录",
                        "编写自定义 SQL 语句"
                    ]
                )

            sql_query = "SELECT * FROM raw_financials LIMIT 10;"
            if sql_template == "查看最新 10 条财务底表数据":
                sql_query = "SELECT * FROM raw_financials ORDER BY fetched_at DESC LIMIT 10;"
            elif sql_template == "查看缓存的汇率底表数据":
                sql_query = "SELECT * FROM exchange_rates ORDER BY fetched_at DESC;"
            elif sql_template == "查看缓存的股价底表数据":
                sql_query = "SELECT * FROM stock_prices ORDER BY fetched_at DESC;"
            elif sql_template == "查看所有成功缓存过的股票输入记录":
                sql_query = "SELECT ticker, provider, fetched_at FROM audit_inputs ORDER BY fetched_at DESC;"
            else:
                sql_query = ""

            with col_sql2:
                custom_sql = st.text_area("SQL 编辑器", value=sql_query, height=100, placeholder="例如: SELECT * FROM raw_financials WHERE ticker = '0700.HK';")
            
            if custom_sql.strip():
                try:
                    with duckdb.connect(DB_PATH, read_only=True) as conn:
                        df_res = conn.execute(custom_sql).df()
                    st.success("SQL 执行成功")
                    st.dataframe(df_res, use_container_width=True)
                except Exception as query_exc:
                    st.error(f"SQL 执行失败: {query_exc}")
        else:
            st.info("缓存数据库 `audit_cache.db` 尚未建立。请从左侧通过 Yahoo 或 Futu 接口拉取并分析任意港股实时数据以进行初始化。")
    except Exception as exc:
        st.error(f"无法初始化 DuckDB 诊断工具: {exc}")


def render_selected_section(section: str, data: CompanyAuditInput, params: AuditParams, result: AuditResult) -> None:
    # If the database contains absolute values, we scale a copy of the results to 'million'口径 for all UI presentation logic!
    if data.amount_unit == "absolute" and section != SECTION_LEDGER:
        import dataclasses
        import copy

        scaled_df = result.audited_df.copy()
        fields_to_scale = [
            "net_profit", "ebit", "interest_expense", "total_equity", 
            "short_term_debt", "long_term_debt", "cash_and_equivalents", 
            "operating_cash_flow", "capex", "da", "dividends_paid", 
            "buybacks_paid", "ma_paid", "goodwill", "shares_outstanding", 
            "buybacks_shares", "Market_Cap", "Owner_Earnings", 
            "maintenance_capex", "total_debt", "Invested_Capital", 
            "Retained_Earnings_Annual", "FCF"
        ]
        for f in fields_to_scale:
            if f in scaled_df.columns:
                scaled_df[f] = scaled_df[f] / 1e6
                
        scaled_calc = copy.copy(result.calculator)
        scaled_calc.df = scaled_calc.df.copy()
        for f in fields_to_scale:
            if f in scaled_calc.df.columns:
                scaled_calc.df[f] = scaled_calc.df[f] / 1e6
                
        result = dataclasses.replace(result, audited_df=scaled_df, calculator=scaled_calc)

    if section == SECTION_CAPITAL_ALLOCATION:
        render_capital_allocation_section(data, result)
    elif section == SECTION_ROIC_ROIIC:
        render_roic_roiic_section(params, result)
    elif section == SECTION_BUYBACK:
        render_buyback_section(data, result)
    elif section == SECTION_MA_GOODWILL:
        render_ma_goodwill_section(data, params, result)
    elif section == SECTION_EARNINGS_QUALITY:
        render_earnings_quality_section(data, result)
    elif section == SECTION_CHECKLIST:
        render_checklist_section(result)
    elif section == SECTION_LEDGER:
        render_ledger_section(data, result)
