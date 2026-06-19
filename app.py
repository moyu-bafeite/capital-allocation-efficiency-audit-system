import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from models.input_schema import CompanyAuditInput
from core.calculator import FinancialCalculator
from core.auditor import ManagementAuditor

# Set page layout and title
st.set_page_config(
    page_title="管理层资本配置效率审计系统",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# Custom css for premium UI feel
st.markdown("""
<style>
    .main {
        background-color: #0f111a;
        color: #ffffff;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.25rem;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #8892b0;
    }
    h1, h2, h3 {
        font-weight: 700 !important;
    }
    .badge-A {
        background-color: #00ffcc;
        color: #0f111a;
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Proactive feature: Downloadable schema template helper
def get_empty_template() -> str:
    template = {
        "ticker": "XXXX.HK",
        "company_name": "示例港股公司",
        "currency": "HKD",
        "years": [2020, 2021, 2022, 2023, 2024],
        "financials": {
            "net_profit": [100.0, 120.0, 150.0, 130.0, 180.0],
            "ebit": [120.0, 140.0, 180.0, 150.0, 210.0],
            "tax_rate": [0.165, 0.165, 0.165, 0.165, 0.165],
            "interest_expense": [5.0, 6.0, 7.0, 8.0, 9.0],
            "total_equity": [800.0, 900.0, 1000.0, 1050.0, 1200.0],
            "short_term_debt": [50.0, 60.0, 70.0, 80.0, 70.0],
            "long_term_debt": [150.0, 180.0, 200.0, 220.0, 210.0],
            "cash_and_equivalents": [200.0, 250.0, 300.0, 280.0, 350.0],
            "operating_cash_flow": [130.0, 150.0, 190.0, 160.0, 220.0],
            "capex": [60.0, 70.0, 80.0, 65.0, 75.0],
            "da": [40.0, 45.0, 50.0, 55.0, 60.0],
            "dividends_paid": [30.0, 40.0, 50.0, 50.0, 60.0],
            "buybacks_paid": [0.0, 0.0, 10.0, 15.0, 30.0],
            "buybacks_shares_m": [0.0, 0.0, 2.0, 3.5, 6.0],
            "ma_paid": [10.0, 20.0, 0.0, 30.0, 15.0],
            "goodwill": [100.0, 115.0, 115.0, 140.0, 150.0],
            "shares_outstanding_m": [100.0, 100.0, 98.0, 94.5, 88.5],
            "avg_stock_price": [10.0, 12.0, 9.0, 8.0, 11.0]
        }
    }
    return json.dumps(template, indent=2, ensure_ascii=False)


# Main App Title
st.markdown("## 📈 管理层资本配置效率审计系统")

# ----------------- SIDEBAR: DATA LOADING & CONTROLS -----------------
st.sidebar.header("📁 数据源选择 & 载入")

# Choose data source
data_source_opt = st.sidebar.selectbox(
    "选择审计标的",
    ["腾讯控股 (00700.HK)", "上传自定义 JSON 数据文件"]
)

raw_data = None

if data_source_opt == "腾讯控股 (00700.HK)":
    try:
        with open("data/tencent_demo.json", "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        st.sidebar.success("成功载入【腾讯控股 (0700.HK)】历史财报数据。")
    except Exception as e:
        st.sidebar.error(f"Demo 数据载入失败: {e}")
else:
    uploaded_file = st.sidebar.file_uploader("上传结构化 JSON 财报文件", type=["json"])
    if uploaded_file is not None:
        try:
            raw_data = json.load(uploaded_file)
            st.sidebar.success("上传成功！")
        except Exception as e:
            st.sidebar.error(f"解析 JSON 失败: {e}")
    else:
        st.sidebar.info("请在上方拖入 JSON 财报文件。")

# Proactive feature: Download Template link in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ 工具箱")
st.sidebar.download_button(
    label="⬇️ 下载 JSON 财报输入模板",
    data=get_empty_template(),
    file_name="capital_allocation_template.json",
    mime="application/json"
)

# Ensure we have loaded data before continuing
if raw_data is None:
    st.info("💡 请在侧边栏选择腾讯 Demo 数据或上传自定义 JSON 数据启动系统。")
    st.stop()

# Parse and validate through Pydantic Schema
try:
    validated_input = CompanyAuditInput(**raw_data)
except Exception as e:
    st.error(f"❌ 数据结构校验失败，请检查字段格式。详细错误: {e}")
    st.stop()

# ----------------- SIDEBAR: AUDIT PARAMETERS -----------------
st.sidebar.markdown("---")
st.sidebar.header("⚙️ 审计与估值模型参数")

st.sidebar.subheader("1. 维持性资本支出")
maint_capex_ratio = st.sidebar.slider(
    "维持性 CapEx 占总资本开支比例",
    min_value=0.10,
    max_value=1.00,
    value=0.50,
    step=0.05,
    help="巴菲特定义“所有者盈余”时需扣除维持目前业务所需资本开支 (Maintenance CapEx)。财报中一般未披露，50% 为保守默认估算值。"
)

st.sidebar.subheader("2. ROIIC 滚动窗口与滞后参数")
num_years = len(validated_input.years)
max_roiic_window = max(1, num_years - 1)

roiic_window_1 = st.sidebar.number_input(
    "ROIIC 短窗口年数",
    min_value=1,
    max_value=max_roiic_window,
    value=min(3, max_roiic_window),
    step=1,
    help="用于生成第一个 ROIIC / ROIIC Retained 滚动窗口，默认 3 年。"
)

roiic_window_2 = st.sidebar.number_input(
    "ROIIC 长窗口年数",
    min_value=1,
    max_value=max_roiic_window,
    value=min(5, max_roiic_window),
    step=1,
    help="用于生成第二个 ROIIC / ROIIC Retained 滚动窗口，默认 5 年。"
)

max_roiic_retained_lag = max(0, num_years - max(roiic_window_1, roiic_window_2))
roiic_retained_lag = st.sidebar.number_input(
    "ROIIC Retained 留存收益滞后年数",
    min_value=0,
    max_value=max_roiic_retained_lag,
    value=min(1, max_roiic_retained_lag),
    step=1,
    help="lag=1 时，计算 T+3 的 3 年 ROIIC Retained 会使用 T、T+1、T+2 的累计留存收益。"
)

st.sidebar.subheader("3. 两阶段 DCF 估值模型参数")
wacc = st.sidebar.slider(
    "折现率 (WACC / 机会成本)",
    min_value=0.05,
    max_value=0.15,
    value=0.08,
    step=0.005,
    format="%.3f"
)

growth_s1 = st.sidebar.slider(
    "第一阶段增长率（前 5 年）",
    min_value=-0.10,
    max_value=0.30,
    value=0.08,
    step=0.01,
    format="%.2f"
)

growth_s2 = st.sidebar.slider(
    "第二阶段增长率（后 5 年）",
    min_value=-0.10,
    max_value=0.20,
    value=0.04,
    step=0.01,
    format="%.2f"
)

terminal_g = st.sidebar.slider(
    "永续增长率 (Terminal Growth)",
    min_value=0.00,
    max_value=0.05,
    value=0.02,
    step=0.005,
    format="%.3f"
)

# Initialize engines
calc = FinancialCalculator(validated_input, maintenance_capex_ratio=maint_capex_ratio)
processed_df = calc.get_processed_df(
    roiic_window_1=roiic_window_1,
    roiic_window_2=roiic_window_2,
    roiic_retained_lag=roiic_retained_lag
)
roiic_retained_col_1 = f"ROIIC_Retained_{roiic_window_1}Y"
roiic_retained_col_2 = f"ROIIC_Retained_{roiic_window_2}Y"

auditor = ManagementAuditor(processed_df)
# Compute intrinsic values under custom DCF
auditor.calculate_intrinsic_value(
    wacc=wacc,
    growth_stage_1=growth_s1,
    stage_1_years=5,
    growth_stage_2=growth_s2,
    stage_2_years=5,
    terminal_growth=terminal_g
)
# Audit buybacks
audited_df = auditor.audit_buybacks()
# Scorecard
scorecard = auditor.generate_scorecard()
# Commentary
commentary = auditor.generate_commentary(scorecard)


# ----------------- MAIN PANEL: METADATA & SUMMARY -----------------
col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
with col_meta1:
    st.metric("标的名称 / 代码", f"{validated_input.company_name} / {validated_input.ticker}")
with col_meta2:
    st.metric("统计年限", f"{validated_input.years[0]}-{validated_input.years[-1]} ({len(validated_input.years)})")
with col_meta3:
    st.metric("财报本位币", validated_input.currency)
with col_meta4:
    st.metric("审计综合等级", f"🏆 {scorecard['grade']}", f"得分: {scorecard['composite_score']}/100")

st.markdown("---")

# Dropdown navigation
selected_section = st.selectbox(
    "🔍 选择审计分析维度 (Audit Dimensions)",
    [
        "📊 累计资本分配流向 (Cumulative Capital Allocation / Sources & Uses)",
        "🚀 存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)",
        "🎁 股份回购与红利分配 (Share Repurchase & Dividend Efficacy)",
        "🏆 资本配置能力综合量化评分 (Capital Allocation Scorecard)",
        "📋 财务数据标准化原始审计底表 (Standardized Financial Indicator Ledger)"
    ]
)

# ----------------- TAB 1: CAPITAL ALLOCATION WATERFALL -----------------
if selected_section == "📊 累计资本分配流向 (Cumulative Capital Allocation / Sources & Uses)":
    st.markdown("#### 📊 累计资本分配流向 (Cumulative Capital Allocation / Sources & Uses)")
    
    # Sub-selector for Custom range or single year
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        time_mode = st.radio(
            "选择时间范围维度 (Select Time Scope)",
            ["📅 任意区间累计分析 (Custom Cumulative Period)", "🗓️ 单一年度专项审计 (Single Fiscal Year Audit)"],
            index=0
        )
    
    years = validated_input.years
    start_yr = min(years)
    end_yr = max(years)
    
    with col_sel2:
        if time_mode == "📅 任意区间累计分析 (Custom Cumulative Period)":
            selected_years = st.slider(
                "选择时间区间 (Select Year Range)",
                min_value=int(start_yr),
                max_value=int(end_yr),
                value=(int(start_yr), int(end_yr)),
                step=1
            )
            start_year_selected = selected_years[0]
            end_year_selected = selected_years[1]
            st.info(f"📍 当前区间：**{start_year_selected} - {end_year_selected} ({end_year_selected - start_year_selected + 1})**")
        else:
            selected_year = st.selectbox(
                "选择单年度 (Select Fiscal Year)",
                years,
                index=len(years) - 1
            )
            start_year_selected = selected_year
            end_year_selected = selected_year
            st.info(f"📍 当前单年度：**{selected_year}**")

    if start_year_selected == end_year_selected:
        st.markdown(f"追踪 **{start_year_selected}** 单一年度公司通过**经营活动赚取的现金流**，审计管理层是如何将它们在**资本支出 (CapEx)、现金分红、回购股份、投资并购**等渠道间进行分配的。")
    else:
        st.markdown(f"追踪 **{start_year_selected}-{end_year_selected}** 年累计期间公司通过**经营活动赚取的累计现金流**，审计管理层是如何将它们在**资本支出 (CapEx)、现金分红、回购股份、投资并购**等渠道间进行分配的。")
    
    waterfall_data = calc.get_waterfall_data(start_year_selected, end_year_selected)
    
    # Render Plotly Waterfall Chart
    x_labels = ["经营现金流 (总流入)", "资本支出 (CapEx)", "现金分红", "股份回购", "投资与并购", "其他现金/债务留存"]
    y_values = [
        waterfall_data["Total_Operating_Cash_Flow"],
        -waterfall_data["CapEx"],
        -waterfall_data["Dividends"],
        -waterfall_data["Buybacks"],
        -waterfall_data["M_and_A"],
        -waterfall_data["Other_Retention"]
    ]
    
    # Determine appropriate scaling and unit label
    max_val = max(abs(val) for val in y_values)
    if max_val >= 1000:
        scale = 1000.0
        unit_label = "Billions"
        suffix = "B"
    else:
        scale = 1.0
        unit_label = "Millions"
        suffix = "M"

    measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="Capital Flow",
        orientation="v",
        measure=measure,
        x=x_labels,
        textposition="outside",
        text=[f"{val/scale:.1f}{suffix}" for val in y_values],
        y=y_values,
        connector={"line": {"color": "rgb(63, 63, 63)", "width": 1.5}},
        decreasing={"marker": {"color": "#ff4d4d"}},
        increasing={"marker": {"color": "#00ffcc"}},
        totals={"marker": {"color": "#3399ff"}}
    ))
    
    title_text = f"{start_year_selected} - {end_year_selected} 年累计资本分配去向瀑布图（单位：{unit_label}）" if start_year_selected != end_year_selected else f"{start_year_selected} 年度单年资本分配去向瀑布图（单位：{unit_label}）"
    fig_waterfall.update_layout(
        title=title_text,
        waterfallgap=0.3,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=500
    )
    
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        st.plotly_chart(fig_waterfall, use_container_width=True)
    with col_w2:
        st.markdown("###### 资本流向构成比率")
        # Pie chart for allocation breakdown
        pie_labels = ["资本支出(CapEx)", "现金分红", "股份回购", "投资并购", "其他现金/债务留存"]
        pie_values = [
            waterfall_data["CapEx"],
            waterfall_data["Dividends"],
            waterfall_data["Buybacks"],
            waterfall_data["M_and_A"],
            max(0, waterfall_data["Other_Retention"])
        ]
        pie_colors = ["#10B981", "#3B82F6", "#EC4899", "#F59E0B", "#6B7280"]
        fig_pie = px.pie(
            names=pie_labels,
            values=pie_values,
            hole=0.4,
            color_discrete_sequence=pie_colors
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ffffff"),
            height=350,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Key statistics cards
    st.markdown("###### 🎯 资本分配率诊断")
    c1, c2, c3, c4 = st.columns(4)
    total_ocf = waterfall_data["Total_Operating_Cash_Flow"]
    with c1:
        st.metric("CapEx 占 OCF 比例", f"{(waterfall_data['CapEx']/total_ocf)*100:.1f}%", help="企业重资产程度。该比例越低，说明企业创造自由现金流的‘血能’越强。")
    with c2:
        st.metric("现金分红率", f"{(waterfall_data['Dividends']/total_ocf)*100:.1f}%", help="分配给股东的现金比例。")
    with c3:
        st.metric("股份回购率", f"{(waterfall_data['Buybacks']/total_ocf)*100:.1f}%", help="利用多余现金在公开市场回购股份注销的力度。")
    with c4:
        st.metric("并购与投资比率", f"{(waterfall_data['M_and_A']/total_ocf)*100:.1f}%", help="管理层通过投资/并购外部实体实现增长的力度。若该数值过高但后续 ROIIC 极低，则是管理层盲目扩张的信号。")


# ----------------- TAB 2: ROIC & ROIIC -----------------
elif selected_section == "🚀 存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)":
    st.markdown("#### 🚀 存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)")
    st.markdown("""
    巴菲特强调：投资人不仅要看当前的存量资本回报率 (ROIC)，更要看管理层“截留利润进行再投资”时的增量回报率 (ROIIC)。
    *   **ROIC（存量回报率）**： 衡量目前公司已投入资本的运营效率。
    *   **ROIIC Retained（留存再投资回报率）**： $\Delta NOPAT / 累计留存盈余$。衡量管理层扣留盈利后，再投资的效率。
    """)

    # Multi-line plot for ROIC and ROIIC
    fig_roic = go.Figure()
    
    # 1. ROIC
    fig_roic.add_trace(go.Scatter(
        x=audited_df.index,
        y=audited_df["ROIC"],
        mode="lines+markers",
        name="ROIC（存量回报率）",
        line=dict(color="#10B981", width=3),
        marker=dict(size=8, color="#10B981")
    ))
    
    # 2. ROIIC retained short window
    fig_roic.add_trace(go.Scatter(
        x=audited_df.index,
        y=audited_df[roiic_retained_col_1],
        mode="lines+markers",
        name=f"ROIIC Retained（{roiic_window_1} 年滚动增量，滞后 {roiic_retained_lag} 年）",
        line=dict(color="#3399ff", width=2, dash="dash"),
        marker=dict(size=6)
    ))

    # 3. ROIIC retained long window
    if roiic_retained_col_2 != roiic_retained_col_1:
        fig_roic.add_trace(go.Scatter(
            x=audited_df.index,
            y=audited_df[roiic_retained_col_2],
            mode="lines+markers",
            name=f"ROIIC Retained（{roiic_window_2} 年滚动增量，滞后 {roiic_retained_lag} 年）",
            line=dict(color="#ff9900", width=2.5, dash="dot"),
            marker=dict(size=6)
        ))

    fig_roic.update_layout(
        title="ROIC 与 ROIIC（留存盈余视角）趋势",
        xaxis_title="年份",
        yaxis_title="回报率",
        xaxis=dict(
            tickmode="linear",
            tick0=min(audited_df.index),
            dtick=1
        ),
        yaxis=dict(tickformat=".1%"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        )
    )
    st.plotly_chart(fig_roic, use_container_width=True)

    # Analysis Commentary
    st.info("""
    💡 **指引**：
    1. 若 **ROIC 长期维持在 15% 以上**，表明公司产品或服务具备极强的“护城河”，是优质资产。
    2. 若 **ROIIC 大幅低于 ROIC**，表明公司随着业务规模成熟，高回报的新投资机会已经枯竭。此时管理层**最明智的举措是加大分红与回购**，而不是固执地留存资金进行低效再投资。
    """)


# ----------------- TAB 3: SHAREHOLDER RETURN & BUYBACKS -----------------
elif selected_section == "🎁 股份回购与红利分配 (Share Repurchase & Dividend Efficacy)":
    st.markdown("#### 🎁 股份回购与红利分配 (Share Repurchase & Dividend Efficacy)")
    st.markdown("许多管理层在牛市顶峰高估值时跟风大额回购（摧毁股东价值），在熊市低谷时却停止回购。本模块对比**实际回购成交均价和**保守每股内在价值 (DCF)**，甄别管理层是在**低吸创造复利**，还是在**高位接盘毁灭价值**。")

    # Double Axis Line Chart
    fig_buyback = go.Figure()
    
    # Intrinsic Value
    fig_buyback.add_trace(go.Scatter(
        x=audited_df.index,
        y=audited_df["Intrinsic_Value_Share"],
        mode="lines+markers",
        name="保守每股内在价值（估值锚点）",
        line=dict(color="#00ffcc", width=3),
        marker=dict(size=8)
    ))
    
    # Average Stock Price
    fig_buyback.add_trace(go.Scatter(
        x=audited_df.index,
        y=audited_df["avg_stock_price"],
        mode="lines+markers",
        name="年平均交易股价",
        line=dict(color="#8892b0", width=1.5, dash="dash"),
        marker=dict(size=5)
    ))

    # Actual Buyback Price (only show points where buyback took place)
    buyback_active = audited_df[audited_df["Buyback_Price_Share"] > 0]
    fig_buyback.add_trace(go.Scatter(
        x=buyback_active.index,
        y=buyback_active["Buyback_Price_Share"],
        mode="markers",
        name="实际股份回购均价",
        marker=dict(color="#ff3366", size=12, symbol="triangle-up", line=dict(color="#ffffff", width=1.5))
    ))

    fig_buyback.update_layout(
        title="每股内在价值（估值锚） vs. 年度均价 vs. 实际回购成交价",
        xaxis_title="年份",
        yaxis_title=f"价格 ({validated_input.currency})",
        xaxis=dict(
            tickmode="linear",
            tick0=min(audited_df.index),
            dtick=1
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=500
    )
    st.plotly_chart(fig_buyback, use_container_width=True)

    # Buyback Audit Table
    st.markdown("###### 📝 历年回购决策审计明细")
    audit_display_df = audited_df[[
        "dividends_paid", "buybacks_paid", "buybacks_shares_m", 
        "Buyback_Price_Share", "Intrinsic_Value_Share", "Buyback_to_Intrinsic_Ratio", "Buyback_Audit_Rating"
    ]].copy()
    
    # Rename for professional look
    audit_display_df.columns = [
        "现金派息总额", "回购现金支出", "回购股份数量（百万股）", 
        "实际回购均价", "每股估算内在价值", "回购均价 / 内在价值", "回购效率审计结论"
    ]
    
    # Formatting
    st.dataframe(
        audit_display_df.style.format({
            "现金派息总额": "{:,.1f}",
            "回购现金支出": "{:,.1f}",
            "回购股份数量（百万股）": "{:,.2f}",
            "实际回购均价": "{:,.2f}",
            "每股估算内在价值": "{:,.2f}",
            "回购均价/内在价值": "{:.2%}"
        }).map(
            lambda x: "color: #00ffcc; font-weight: bold;" if "卓越" in str(x)
            else "color: #ff4d4d; font-weight: bold;" if "盲目" in str(x)
            else "color: #8892b0;" if "无显著" in str(x)
            else "",
            subset=["回购效率审计结论"]
        ),
        use_container_width=True
    )


# ----------------- TAB 4: SCORECARD & ADVICE -----------------
elif selected_section == "🏆 资本配置能力综合量化评分 (Capital Allocation Scorecard)":
    st.markdown("#### 🏆 资本配置能力综合量化评分 (Capital Allocation Scorecard)")
    st.markdown("结合定量算法，对增量再投资能力、一美元创造效率、回购纪律及股东派息慷慨度进行多维度加权打分：")

    col_score1, col_score2 = st.columns([1, 2])
    
    with col_score1:
        st.markdown(f"""
        <div style="background-color: #171923; padding: 2rem; border-radius: 1rem; border: 2px solid #00ffcc; text-align: center;">
            <p style="font-size: 1.2rem; color: #8892b0; margin-bottom: 0.5rem;">期末审计评级</p>
            <p style="font-size: 5.5rem; font-weight: 900; color: #00ffcc; margin: 0; line-height: 1;">{scorecard['grade']}</p>
            <p style="font-size: 1.5rem; color: #ffffff; margin-top: 1rem; font-weight: bold;">综合分： {scorecard['composite_score']}/100</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("-----")
        
        st.markdown("###### 📐 五维权重分值细目")
        st.markdown(f"- 存量资产创利 (30%)：**{scorecard['roic_score']:.0f}**")
        st.markdown(f"- 增量利润开拓 (25%)：**{scorecard['roiic_score']:.0f}**")
        st.markdown(f"- 市场市值创造 (20%)：**{scorecard['one_dollar_score']:.0f}**")
        st.markdown(f"- 回购折价溢价 (10%)：**{scorecard['buyback_score']:.0f}**")
        st.markdown(f"- 现金回报适配 (15%)：**{scorecard['payout_score']:.0f}**")

    with col_score2:
        st.markdown(commentary)


# ----------------- TAB 5: FINANCIAL TABLES -----------------
elif selected_section == "📋 财务数据标准化原始审计底表 (Standardized Financial Indicator Ledger)":
    st.markdown("#### 📋 审计模型处理底表数据 (Raw Data & Intermediaries)")
    st.markdown("以下为系统输入参数以及计算得出的所有核心中间指标：")
    
    # Exclude or re-arrange columns to make it readable
    st.dataframe(processed_df.style.format("{:,.2f}"), use_container_width=True)
    
    st.download_button(
        label="📥 导出审计表格为 CSV",
        data=processed_df.to_csv().encode('utf-8-sig'),
        file_name=f"capital_allocation_audit_{validated_input.ticker}.csv",
        mime="text/csv"
    )
