import json
from typing import Tuple

import streamlit as st

from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams


def get_empty_template() -> str:
    template = {
        "ticker": "XXXX.HK",
        "company_name": "示例港股公司",
        "currency": "HKD",
        "amount_unit": "million",
        "market_currency": "HKD",
        "exchange_rate_to_reporting_currency": [1.0, 1.0, 1.0, 1.0, 1.0],
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
            "avg_stock_price": [10.0, 12.0, 9.0, 8.0, 11.0],
        },
    }
    return json.dumps(template, indent=2, ensure_ascii=False)


def _load_raw_data() -> dict | None:
    st.sidebar.header("📁 数据源选择 & 载入")
    data_source_opt = st.sidebar.selectbox(
        "选择审计标的",
        ["腾讯控股 (00700.HK)", "上传自定义 JSON 数据文件"],
    )

    if data_source_opt == "腾讯控股 (00700.HK)":
        try:
            with open("data/tencent_demo.json", "r", encoding="utf-8") as file:
                raw_data = json.load(file)
            st.sidebar.success("成功载入【腾讯控股 (0700.HK)】历史财报数据。")
            return raw_data
        except Exception as exc:
            st.sidebar.error(f"Demo 数据载入失败: {exc}")
            return None

    uploaded_file = st.sidebar.file_uploader("上传结构化 JSON 财报文件", type=["json"])
    if uploaded_file is None:
        st.sidebar.info("请在上方拖入 JSON 财报文件。")
        return None

    try:
        raw_data = json.load(uploaded_file)
        st.sidebar.success("上传成功！")
        return raw_data
    except Exception as exc:
        st.sidebar.error(f"解析 JSON 失败: {exc}")
        return None


def _render_toolbox() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ 工具箱")
    st.sidebar.download_button(
        label="⬇️ 下载 JSON 财报输入模板",
        data=get_empty_template(),
        file_name="capital_allocation_template.json",
        mime="application/json",
    )


def _parse_input(raw_data: dict | None) -> CompanyAuditInput:
    if raw_data is None:
        st.info("💡 请在侧边栏选择腾讯 Demo 数据或上传自定义 JSON 数据启动系统。")
        st.stop()

    try:
        return CompanyAuditInput(**raw_data)
    except Exception as exc:
        st.error(f"❌ 数据结构校验失败，请检查字段格式。详细错误: {exc}")
        st.stop()


def _render_params(data: CompanyAuditInput) -> AuditParams:
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 审计与估值模型参数")

    st.sidebar.subheader("1. 维持性资本支出")
    maintenance_capex_ratio = st.sidebar.slider(
        "维持性 CapEx 占总资本开支比例",
        min_value=0.10,
        max_value=1.00,
        value=0.50,
        step=0.05,
        help="巴菲特定义“所有者盈余”时需扣除维持目前业务所需资本开支 (Maintenance CapEx)。财报中一般未披露，50% 为保守默认估算值。",
    )

    st.sidebar.subheader("2. ROIIC 滚动窗口与滞后参数")
    num_years = len(data.years)
    max_roiic_window = max(1, num_years - 1)
    roiic_window_1 = int(
        st.sidebar.number_input(
            "ROIIC 短窗口年数",
            min_value=1,
            max_value=max_roiic_window,
            value=min(3, max_roiic_window),
            step=1,
            help="用于生成第一个 ROIIC / ROIIC Retained 滚动窗口，默认 3 年。",
        )
    )
    roiic_window_2 = int(
        st.sidebar.number_input(
            "ROIIC 长窗口年数",
            min_value=1,
            max_value=max_roiic_window,
            value=min(5, max_roiic_window),
            step=1,
            help="用于生成第二个 ROIIC / ROIIC Retained 滚动窗口，默认 5 年。",
        )
    )
    max_roiic_retained_lag = max(0, num_years - max(roiic_window_1, roiic_window_2))
    roiic_retained_lag = int(
        st.sidebar.number_input(
            "ROIIC Retained 留存收益滞后年数",
            min_value=0,
            max_value=max_roiic_retained_lag,
            value=min(1, max_roiic_retained_lag),
            step=1,
            help="lag=1 时，计算 T+3 的 3 年 ROIIC Retained 会使用 T、T+1、T+2 的累计留存收益。",
        )
    )

    st.sidebar.subheader("3. 两阶段 DCF 估值模型参数")
    wacc = st.sidebar.slider(
        "折现率 (WACC / 机会成本)",
        min_value=0.05,
        max_value=0.15,
        value=0.08,
        step=0.005,
        format="%.3f",
    )
    growth_stage_1 = st.sidebar.slider(
        "第一阶段增长率（前 5 年）",
        min_value=-0.10,
        max_value=0.30,
        value=0.08,
        step=0.01,
        format="%.2f",
    )
    growth_stage_2 = st.sidebar.slider(
        "第二阶段增长率（后 5 年）",
        min_value=-0.10,
        max_value=0.20,
        value=0.04,
        step=0.01,
        format="%.2f",
    )
    terminal_growth = st.sidebar.slider(
        "永续增长率 (Terminal Growth)",
        min_value=0.00,
        max_value=0.05,
        value=0.02,
        step=0.005,
        format="%.3f",
    )

    if wacc <= terminal_growth:
        st.sidebar.error("折现率 WACC 必须大于永续增长率。")
        st.stop()

    return AuditParams(
        maintenance_capex_ratio=maintenance_capex_ratio,
        roiic_window_1=roiic_window_1,
        roiic_window_2=roiic_window_2,
        roiic_retained_lag=roiic_retained_lag,
        wacc=wacc,
        growth_stage_1=growth_stage_1,
        growth_stage_2=growth_stage_2,
        terminal_growth=terminal_growth,
    )


def render_sidebar() -> Tuple[CompanyAuditInput, AuditParams]:
    raw_data = _load_raw_data()
    _render_toolbox()
    data = _parse_input(raw_data)
    params = _render_params(data)
    return data, params
