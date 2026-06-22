import json
from typing import Tuple
import streamlit as st
from models.input_schema import CompanyAuditInput
from services.audit_pipeline import AuditParams
from data.manager import DataManager

def get_empty_template() -> str:
    template = {
        "ticker": "XXXX.HK",
        "company_name": "示例港股公司",
        "currency": "HKD",
        "amount_unit": "absolute",
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
            "buybacks_shares": [0.0, 0.0, 2000000.0, 3500000.0, 6000000.0],
            "ma_paid": [10.0, 20.0, 0.0, 30.0, 15.0],
            "goodwill": [100.0, 115.0, 115.0, 140.0, 150.0],
            "shares_outstanding": [100000000.0, 100000000.0, 98000000.0, 94500000.0, 88500000.0],
            "avg_stock_price": [10.0, 12.0, 9.0, 8.0, 11.0],
        },
    }
    return json.dumps(template, indent=2, ensure_ascii=False)

def _render_toolbox() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ 工具箱")
    st.sidebar.download_button(
        label="⬇️ 下载 JSON 财报输入模板",
        data=get_empty_template(),
        file_name="capital_allocation_template.json",
        mime="application/json",
    )

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
    st.sidebar.header("📁 数据源选择 & 载入")
    data_source_opt = st.sidebar.selectbox(
        "选择审计标的",
        [
            "从 富途牛牛 (Futu OpenD) 实时拉取",
            # "从 雅虎财经 (Yahoo Finance) 实时拉取",
            "上传自定义 JSON 数据文件"
        ],
    )

    # Initialize variables
    data_obj = None

    # Handle source selection
    if data_source_opt == "上传自定义 JSON 数据文件":
        uploaded_file = st.sidebar.file_uploader("上传结构化 JSON 财报文件", type=["json"])
        if uploaded_file is not None:
            try:
                raw_data = json.load(uploaded_file)
                data_obj = CompanyAuditInput(**raw_data)
                st.sidebar.success("上传成功！")
            except Exception as exc:
                st.sidebar.error(f"解析/校验 JSON 失败: {exc}")
                st.stop()
        else:
            st.info("💡 请在侧边栏上传 JSON 财报文件启动审计系统。")
            st.stop()

    else:
        # Live APIs (Yahoo or Futu)
        is_yahoo = "Yahoo" in data_source_opt
        provider_name = "yahoo" if is_yahoo else "futu"
        default_ticker = "0700.HK" if is_yahoo else "HK.00700"

        ticker_input = st.sidebar.text_input("输入港股代码", value=default_ticker, help="例如: 0700.HK, 9988.HK 或 HK.00700").strip()
        
        # Years Slider selection
        years_range = st.sidebar.slider(
            "选择财报审计年份区间",
            min_value=2010,
            max_value=2025,
            value=(2016, 2025),
            step=1
        )
        years_list = list(range(years_range[0], years_range[1] + 1))
        
        force_refresh = st.sidebar.checkbox("强制刷新本地数据库缓存", value=False)
        fetch_btn = st.sidebar.button("🔍 开始实时拉取并审计")

        # Create source signature key
        source_key = f"{ticker_input}_{provider_name}_{years_range[0]}_{years_range[1]}"

        # 1. Memory/Session Cache check
        if not force_refresh and "cached_input_data" in st.session_state and st.session_state.get("cached_source_key") == source_key:
            data_obj = st.session_state["cached_input_data"]
        else:
            # 2. DuckDB Disk Cache check
            manager = DataManager()
            cached_dict = None
            if not force_refresh:
                cached_dict = manager.cache.get_audit_input(ticker_input, provider_name)
                
            if cached_dict and set(years_list).issubset(set(cached_dict.get("years", []))):
                try:
                    data_obj = CompanyAuditInput(**cached_dict)
                    st.session_state["cached_input_data"] = data_obj
                    st.session_state["cached_source_key"] = source_key
                    st.sidebar.success(f"成功从本地 DuckDB 缓存载入 {ticker_input}。")
                except Exception:
                    cached_dict = None

            # 3. Pull fresh from API if cache misses or refresh is requested
            if data_obj is None:
                if fetch_btn:
                    try:
                        with st.spinner("正在从 API 抓取财报并保存到本地 DuckDB..."):
                            data_obj = manager.get_audit_input(
                                ticker=ticker_input,
                                provider_name=provider_name,
                                years=years_list,
                                refresh=True
                            )
                        st.session_state["cached_input_data"] = data_obj
                        st.session_state["cached_source_key"] = source_key
                        st.sidebar.success(f"成功获取 {ticker_input} 数据并缓存至本地！")
                    except Exception as exc:
                        st.sidebar.error(f"数据抓取 / 标准化失败：{exc}")
                        st.stop()
                else:
                    st.info("💡 缓存未命中。请点击【开始实时拉取并审计】按钮以从 API 抓取并加载。")
                    st.stop()

    _render_toolbox()
    params = _render_params(data_obj)
    return data_obj, params
