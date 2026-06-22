import streamlit as st

from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams, AuditResult
from ui.charts import (
    create_allocation_pie_chart,
    create_buyback_chart,
    create_roic_chart,
    create_waterfall_chart,
)


SECTION_CAPITAL_ALLOCATION = "📊 累计资本分配流向 (Cumulative Capital Allocation / Sources & Uses)"
SECTION_ROIC_ROIIC = "🚀 存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)"
SECTION_BUYBACK = "🎁 股份回购与红利分配 (Share Repurchase & Dividend Efficacy)"
SECTION_SCORECARD = "🏆 资本配置能力综合量化评分 (Capital Allocation Scorecard)"
SECTION_LEDGER = "📋 财务数据标准化原始审计底表 (Standardized Financial Indicator Ledger)"
SECTIONS = [SECTION_CAPITAL_ALLOCATION, SECTION_ROIC_ROIIC, SECTION_BUYBACK, SECTION_SCORECARD, SECTION_LEDGER]


def render_summary(data: CompanyAuditInput, scorecard: dict) -> None:
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.metric("标的名称 / 代码", f"{data.company_name} / {data.ticker}")
    with col_meta2:
        st.metric("统计年限", f"{data.years[0]}-{data.years[-1]} ({len(data.years)})")
    with col_meta3:
        display_unit = "元（原始值）" if data.amount_unit == "absolute" else data.amount_unit
        st.metric("财报币种 / 金额单位", f"{data.currency} / {display_unit}", f"市场币种: {data.market_currency}")
    with col_meta4:
        st.metric("审计综合等级", f"🏆 {scorecard['grade']}", f"得分: {scorecard['composite_score']}/100")
    st.markdown("---")


def render_navigation() -> str:
    return st.selectbox("🔍 选择审计分析维度 (Audit Dimensions)", SECTIONS)


def render_capital_allocation_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 📊 累计资本分配流向 (Cumulative Capital Allocation / Sources & Uses)")

    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        time_mode = st.radio(
            "选择时间范围维度 (Select Time Scope)",
            ["📅 任意区间累计分析 (Custom Cumulative Period)", "🗓️ 单一年度专项审计 (Single Fiscal Year Audit)"],
            index=0,
        )

    years = data.years
    start_year = min(years)
    end_year = max(years)
    with col_sel2:
        if time_mode == "📅 任意区间累计分析 (Custom Cumulative Period)":
            selected_years = st.slider(
                "选择时间区间 (Select Year Range)",
                min_value=int(start_year),
                max_value=int(end_year),
                value=(int(start_year), int(end_year)),
                step=1,
            )
            start_year_selected = selected_years[0]
            end_year_selected = selected_years[1]
            st.info(f"📍 当前区间：**{start_year_selected} - {end_year_selected} ({end_year_selected - start_year_selected + 1})**")
        else:
            selected_year = st.selectbox("选择单年度 (Select Fiscal Year)", years, index=len(years) - 1)
            start_year_selected = selected_year
            end_year_selected = selected_year
            st.info(f"📍 当前单年度：**{selected_year}**")

    if start_year_selected == end_year_selected:
        st.markdown(f"追踪 **{start_year_selected}** 单一年度公司通过**经营活动赚取的现金流**，审计管理层如何在**资本支出、现金分红、回购股份、投资并购**等渠道间分配资本。")
    else:
        st.markdown(f"追踪 **{start_year_selected}-{end_year_selected}** 年累计期间公司通过**经营活动赚取的累计现金流**，审计管理层如何在**资本支出、现金分红、回购股份、投资并购**等渠道间分配资本。")

    waterfall_data = result.calculator.get_waterfall_data(start_year_selected, end_year_selected)
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        st.plotly_chart(create_waterfall_chart(waterfall_data, start_year_selected, end_year_selected), use_container_width=True)
    with col_w2:
        st.markdown("###### 资本流向构成比率")
        st.plotly_chart(create_allocation_pie_chart(waterfall_data), use_container_width=True)

    st.markdown("###### 🎯 资本分配率诊断")
    c1, c2, c3, c4 = st.columns(4)
    total_ocf = waterfall_data["Total_Operating_Cash_Flow"]
    with c1:
        st.metric("CapEx 占 OCF 比例", f"{(waterfall_data['CapEx'] / total_ocf) * 100:.1f}%", help="企业重资产程度。该比例越低，说明企业创造自由现金流的能力越强。")
    with c2:
        st.metric("现金分红率", f"{(waterfall_data['Dividends'] / total_ocf) * 100:.1f}%", help="分配给股东的现金比例。")
    with c3:
        st.metric("股份回购率", f"{(waterfall_data['Buybacks'] / total_ocf) * 100:.1f}%", help="利用多余现金在公开市场回购股份注销的力度。")
    with c4:
        st.metric("并购与投资比率", f"{(waterfall_data['M_and_A'] / total_ocf) * 100:.1f}%", help="管理层通过投资或并购实现增长的力度。若该数值过高但 ROIIC 极低，可能是盲目扩张信号。")


def render_roic_roiic_section(params: AuditParams, result: AuditResult) -> None:
    st.markdown("#### 🚀 存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)")
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
        💡 **指引**：
        1. 若 **ROIC 长期维持在 15% 以上**，表明公司产品或服务具备较强护城河。
        2. 若 **ROIIC 大幅低于 ROIC**，表明高回报的新投资机会可能正在减少，管理层应更多考虑分红与回购。
        """
    )


def render_buyback_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 🎁 股份回购与红利分配 (Share Repurchase & Dividend Efficacy)")
    st.markdown("本模块对比**实际回购成交均价**和**保守每股内在价值 (DCF)**，甄别管理层是在低估时回购创造复利，还是在高估时回购毁灭价值。")

    display_df = result.audited_df.copy()
    fx_rate = display_df["exchange_rate_to_reporting_currency"]
    display_df["Intrinsic_Value_Share_Market_Currency"] = display_df["Intrinsic_Value_Share"] / fx_rate
    display_df["Buyback_Price_Share_Market_Currency"] = display_df["Buyback_Price_Share"] / fx_rate
    display_df["dividends_paid_market_currency"] = display_df["dividends_paid"] / fx_rate
    display_df["buybacks_paid_market_currency"] = display_df["buybacks_paid"] / fx_rate

    st.plotly_chart(create_buyback_chart(display_df, data.market_currency), use_container_width=True)

    st.markdown("###### 📝 历年回购决策审计明细")
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
    audit_display_df.columns = [
        f"现金派息总额（{data.market_currency}）",
        f"回购现金支出（{data.market_currency}）",
        "回购股份数量（股）",
        f"实际回购均价（{data.market_currency}）",
        f"每股估算内在价值（{data.market_currency}）",
        "回购均价 / 内在价值",
        "回购效率审计结论",
    ]

    st.dataframe(
        audit_display_df.style.format(
            {
                f"现金派息总额（{data.market_currency}）": "{:,.2f}",
                f"回购现金支出（{data.market_currency}）": "{:,.2f}",
                "回购股份数量（股）": "{:,.0f}",
                f"实际回购均价（{data.market_currency}）": "{:,.2f}",
                f"每股估算内在价值（{data.market_currency}）": "{:,.2f}",
                "回购均价 / 内在价值": "{:.2%}",
            }
        ).map(
            lambda value: "color: #00ffcc; font-weight: bold;"
            if "卓越" in str(value)
            else "color: #ff4d4d; font-weight: bold;"
            if "盲目" in str(value)
            else "color: #8892b0;"
            if "无显著" in str(value)
            else "",
            subset=["回购效率审计结论"],
        ),
        use_container_width=True,
    )


def render_scorecard_section(result: AuditResult) -> None:
    scorecard = result.scorecard
    st.markdown("#### 🏆 资本配置能力综合量化评分 (Capital Allocation Scorecard)")
    st.markdown("结合定量算法，对增量再投资能力、一美元创造效率、回购纪律及股东派息慷慨度进行多维度加权打分：")

    col_score1, col_score2 = st.columns([1, 2])
    with col_score1:
        st.markdown(
            f"""
            <div style="background-color: #171923; padding: 2rem; border-radius: 1rem; border: 2px solid #00ffcc; text-align: center;">
                <p style="font-size: 1.2rem; color: #8892b0; margin-bottom: 0.5rem;">期末审计评级</p>
                <p style="font-size: 5.5rem; font-weight: 900; color: #00ffcc; margin: 0; line-height: 1;">{scorecard['grade']}</p>
                <p style="font-size: 1.5rem; color: #ffffff; margin-top: 1rem; font-weight: bold;">综合分： {scorecard['composite_score']}/100</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("-----")
        st.markdown("###### 📐 五维权重分值细目")
        st.markdown(f"- 存量资产创利 (30%)：**{scorecard['roic_score']:.0f}**")
        st.markdown(f"- 增量利润开拓 (25%)：**{scorecard['roiic_score']:.0f}**")
        st.markdown(f"- 市场市值创造 (20%)：**{scorecard['one_dollar_score']:.0f}**")
        st.markdown(f"- 回购折价溢价 (10%)：**{scorecard['buyback_score']:.0f}**")
        st.markdown(f"- 现金回报适配 (15%)：**{scorecard['payout_score']:.0f}**")

    with col_score2:
        st.markdown(result.commentary)


def render_ledger_section(data: CompanyAuditInput, result: AuditResult) -> None:
    st.markdown("#### 📋 审计模型处理底表数据 (Raw Data & Intermediaries)")
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
        label="📥 导出完整审计表格为 CSV",
        data=result.audited_df.to_csv().encode("utf-8-sig"),
        file_name=f"capital_allocation_audit_{data.ticker}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("#### 🔌 本地 DuckDB 缓存数据库实时诊断 (DuckDB SQL Diagnostics)")
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
                    st.success("🎉 SQL 执行成功！")
                    st.dataframe(df_res, use_container_width=True)
                except Exception as query_exc:
                    st.error(f"❌ SQL 执行失败: {query_exc}")
        else:
            st.info("💡 缓存数据库 `audit_cache.db` 尚未建立。请从左侧通过 Yahoo 或 Futu 接口拉取并分析任意港股实时数据以进行初始化。")
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
            "Retained_Earnings_Annual"
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
    elif section == SECTION_SCORECARD:
        render_scorecard_section(result)
    elif section == SECTION_LEDGER:
        render_ledger_section(data, result)
