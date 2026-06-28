TRANSLATIONS = {
    # ── app.py ──────────────────────────────────────────────────────────
    "app.title": {
        "zh": "资本配置审计系统",
        "en": "Capital Allocation Audit System",
    },
    "app.error.audit_failed": {
        "zh": "❌ 审计模型运行失败：{exc}",
        "en": "❌ Audit model execution failed: {exc}",
    },
    "app.nav_caption": {
        "zh": "审计维度",
        "en": "Audit Dimension",
    },

    # ── sidebar ─────────────────────────────────────────────────────────
    "sidebar.language": {
        "zh": "语言",
        "en": "Language",
    },
    "sidebar.toolbox": {
        "zh": "工具箱",
        "en": "Toolbox",
    },
    "sidebar.download_template": {
        "zh": "下载 JSON 财报输入模板",
        "en": "Download JSON Financial Input Template",
    },
    "sidebar.pdf_export_header": {
        "zh": "PDF 报告导出",
        "en": "Export PDF Report",
    },
    "sidebar.pdf_export_button": {
        "zh": "生成 PDF 审计报告",
        "en": "Generate PDF Audit Report",
    },
    "sidebar.pdf_export_building": {
        "zh": "正在生成 PDF 报告，含图表渲染，请稍候...",
        "en": "Building PDF report with charts, please wait...",
    },
    "sidebar.pdf_download": {
        "zh": "下载 PDF 报告",
        "en": "Download PDF Report",
    },
    "sidebar.pdf_export_dep_error": {
        "zh": "缺少 PDF 生成依赖：{exc}。请运行 `pip install weasyprint kaleido` 并安装系统库（macOS: `brew install cairo pango gdk-pixbuf libffi`）。",
        "en": "Missing PDF generation dependency: {exc}. Run `pip install weasyprint kaleido` and install system libs (macOS: `brew install cairo pango gdk-pixbuf libffi`).",
    },
    "sidebar.pdf_export_error": {
        "zh": "PDF 生成失败：{exc}",
        "en": "PDF generation failed: {exc}",
    },
    "sidebar.template.company_name": {
        "zh": "示例港股公司",
        "en": "Sample HK Listed Company",
    },
    "sidebar.params_header": {
        "zh": "审计与估值模型参数",
        "en": "Audit & Valuation Model Parameters",
    },
    "sidebar.params.section1": {
        "zh": "1. 维持性资本支出",
        "en": "1. Maintenance Capital Expenditure",
    },
    "sidebar.params.maintenance_capex_ratio": {
        "zh": "维持性 CapEx 占总资本开支比例",
        "en": "Maintenance CapEx as % of Total CapEx",
    },
    "sidebar.params.maintenance_capex_help": {
        "zh": "巴菲特定义“所有者盈余”时需扣除维持目前业务所需资本开支 (Maintenance CapEx)。财报中一般未披露，50% 为保守默认估算值。",
        "en": "Buffett defines \"Owner Earnings\" by deducting the capex needed to maintain the current business. Since financial statements rarely disclose this figure, 50% is a conservative default estimate.",
    },
    "sidebar.params.section2": {
        "zh": "2. ROIIC 滚动窗口与滞后参数",
        "en": "2. ROIIC Rolling Window & Lag Parameters",
    },
    "sidebar.params.roiic_window_1": {
        "zh": "ROIIC 短窗口年数",
        "en": "ROIIC Short Window (Years)",
    },
    "sidebar.params.roiic_window_1_help": {
        "zh": "用于生成第一个 ROIIC / ROIIC Retained 滚动窗口，默认 3 年。",
        "en": "Used to generate the first ROIIC / ROIIC Retained rolling window. Default: 3 years.",
    },
    "sidebar.params.roiic_window_2": {
        "zh": "ROIIC 长窗口年数",
        "en": "ROIIC Long Window (Years)",
    },
    "sidebar.params.roiic_window_2_help": {
        "zh": "用于生成第二个 ROIIC / ROIIC Retained 滚动窗口，默认 5 年。",
        "en": "Used to generate the second ROIIC / ROIIC Retained rolling window. Default: 5 years.",
    },
    "sidebar.params.roiic_retained_lag": {
        "zh": "ROIIC Retained 留存收益滞后年数",
        "en": "ROIIC Retained Lag (Years)",
    },
    "sidebar.params.roiic_retained_lag_help": {
        "zh": "lag=1 时，计算 T+3 的 3 年 ROIIC Retained 会使用 T、T+1、T+2 的累计留存收益。",
        "en": "When lag=1, a 3-Year ROIIC Retained for year T+3 uses cumulative retained earnings from T, T+1, and T+2.",
    },
    "sidebar.params.section3": {
        "zh": "3. 两阶段 DCF 估值模型参数",
        "en": "3. Two-Stage DCF Valuation Parameters",
    },
    "sidebar.params.wacc": {
        "zh": "折现率 (WACC / 机会成本)",
        "en": "Discount Rate (WACC / Opportunity Cost)",
    },
    "sidebar.params.growth_stage_1": {
        "zh": "第一阶段增长率（前 5 年）",
        "en": "Stage 1 Growth Rate (First 5 Years)",
    },
    "sidebar.params.growth_stage_2": {
        "zh": "第二阶段增长率（后 5 年）",
        "en": "Stage 2 Growth Rate (Next 5 Years)",
    },
    "sidebar.params.terminal_growth": {
        "zh": "永续增长率 (Terminal Growth)",
        "en": "Terminal Growth Rate",
    },
    "sidebar.error.wacc_le_terminal": {
        "zh": "折现率 WACC 必须大于永续增长率。",
        "en": "WACC must be greater than the terminal growth rate.",
    },
    "sidebar.data_source_header": {
        "zh": "数据源选择与载入",
        "en": "Data Source Selection & Loading",
    },
    "sidebar.data_source.label": {
        "zh": "选择审计标的",
        "en": "Select Audit Target",
    },
    "sidebar.data_source.futu": {
        "zh": "从 Futu OpenD 实时拉取",
        "en": "Fetch Live from Futu OpenD",
    },
    "sidebar.data_source.yahoo": {
        "zh": "从 Yahoo Finance 实时拉取",
        "en": "Fetch Live from Yahoo Finance",
    },
    "sidebar.data_source.upload": {
        "zh": "上传自定义 JSON 数据文件",
        "en": "Upload Custom JSON Data File",
    },
    "sidebar.upload.label": {
        "zh": "上传结构化 JSON 财报文件",
        "en": "Upload Structured JSON Financial File",
    },
    "sidebar.upload.success": {
        "zh": "上传成功",
        "en": "Upload Successful",
    },
    "sidebar.upload.parse_error": {
        "zh": "解析/校验 JSON 失败: {exc}",
        "en": "JSON Parse/Validation Failed: {exc}",
    },
    "sidebar.upload.prompt": {
        "zh": "请在侧边栏上传 JSON 财报文件启动审计系统。",
        "en": "Please upload a JSON financial file in the sidebar to start the audit system.",
    },
    "sidebar.futu.ticker_input": {
        "zh": "输入港股代码",
        "en": "Enter HK Stock Code",
    },
    "sidebar.futu.ticker_help": {
        "zh": "例如: 0388.HK, 9988.HK 或 HK.00388",
        "en": "e.g.: 0388.HK, 9988.HK or HK.00388",
    },
    "sidebar.futu.year_range": {
        "zh": "选择财报审计年份区间",
        "en": "Select Financial Year Range",
    },
    "sidebar.futu.force_refresh": {
        "zh": "强制刷新本地数据库缓存",
        "en": "Force Refresh Local Database Cache",
    },
    "sidebar.futu.fetch_btn": {
        "zh": "开始拉取并审计",
        "en": "Fetch & Audit",
    },
    "sidebar.futu.loading": {
        "zh": "正在加载财报数据...",
        "en": "Loading financial data...",
    },
    "sidebar.futu.load_success": {
        "zh": "成功加载 {ticker} ({year_start}-{year_end})",
        "en": "Successfully loaded {ticker} ({year_start}-{year_end})",
    },
    "sidebar.futu.load_error": {
        "zh": "数据加载失败：{exc}",
        "en": "Data loading failed: {exc}",
    },
    "sidebar.futu.start_prompt": {
        "zh": "请在侧边栏调整参数，并点击【开始拉取并审计】按钮开始。",
        "en": "Please adjust parameters in the sidebar and click the [Fetch & Audit] button to start.",
    },

    # ── sections: navigation ─────────────────────────────────────────────
    "section.nav.label": {
        "zh": "选择审计分析维度",
        "en": "Select Audit Dimension",
    },
    "section.nav.capital_allocation": {
        "zh": "累计资本流向 · Capital Allocation",
        "en": "Capital Allocation · 累计资本流向",
    },
    "section.nav.roic_roiic": {
        "zh": "存量与增量回报 · ROIC & ROIIC",
        "en": "ROIC & ROIIC · 存量与增量回报",
    },
    "section.nav.buyback": {
        "zh": "股东回报分配 · Shareholder Returns",
        "en": "Shareholder Returns · 股东回报分配",
    },
    "section.nav.ma_goodwill": {
        "zh": "并购与商誉审计 · M&A & Goodwill",
        "en": "M&A & Goodwill · 并购与商誉审计",
    },
    "section.nav.earnings_quality": {
        "zh": "盈利质量审计 · Earnings Quality",
        "en": "Earnings Quality · 盈利质量审计",
    },
    "section.nav.checklist": {
        "zh": "资本配置清单 · Principles Checklist",
        "en": "Principles Checklist · 资本配置清单",
    },
    "section.nav.ledger": {
        "zh": "原始审计底表 · Raw Ledger",
        "en": "Raw Ledger · 原始审计底表",
    },

    # ── sections: summary ────────────────────────────────────────────────
    "metric.label.company": {
        "zh": "标的名称 / 代码",
        "en": "Company / Ticker",
    },
    "metric.label.years": {
        "zh": "统计年限",
        "en": "Years Covered",
    },
    "metric.label.currency_unit": {
        "zh": "财报币种 / 金额单位",
        "en": "Reporting Currency / Unit",
    },
    "metric.label.market_currency": {
        "zh": "市场币种",
        "en": "Market Currency",
    },
    "metric.unit.absolute": {
        "zh": "元",
        "en": "Raw",
    },

    # ── sections: capital allocation ─────────────────────────────────────
    "section.capital.title": {
        "zh": "累计资本流向 (Cumulative Capital Allocation / Sources & Uses)",
        "en": "Cumulative Capital Allocation (Sources & Uses)",
    },
    "section.capital.time_mode.label": {
        "zh": "选择时间范围维度 (Select Time Scope)",
        "en": "Select Time Scope",
    },
    "section.capital.time_mode.cumulative": {
        "zh": "任意区间累计分析 (Custom Cumulative Period)",
        "en": "Custom Cumulative Period",
    },
    "section.capital.time_mode.single_year": {
        "zh": "单一年度专项审计 (Single Fiscal Year Audit)",
        "en": "Single Fiscal Year Audit",
    },
    "section.capital.year_range": {
        "zh": "选择时间区间 (Select Year Range)",
        "en": "Select Year Range",
    },
    "section.capital.current_range": {
        "zh": "当前区间：**{start_year} - {end_year} ({n_years})**",
        "en": "Current Range: **{start_year} - {end_year} ({n_years})**",
    },
    "section.capital.single_year.label": {
        "zh": "选择单年度 (Select Fiscal Year)",
        "en": "Select Fiscal Year",
    },
    "section.capital.current_single_year": {
        "zh": "当前单年度：**{year}**",
        "en": "Current Fiscal Year: **{year}**",
    },
    "section.capital.desc.single_year": {
        "zh": "追踪 **{year}** 单一年度公司通过**经营活动赚取的现金流**，审计管理层如何在**资本支出、现金分红、回购股份、投资并购**等渠道间分配资本。",
        "en": "Tracking the cash flow generated from **operations in FY {year}** and auditing how management allocates capital across **CapEx, dividends, buybacks, and M&A**.",
    },
    "section.capital.desc.cumulative": {
        "zh": "追踪 **{start_year}-{end_year}** 年累计期间公司通过**经营活动赚取的累计现金流**，审计管理层如何在**资本支出、现金分红、回购股份、投资并购**等渠道间分配资本。",
        "en": "Tracking the cumulative cash flow generated from **operations during {start_year}-{end_year}** and auditing how management allocates capital across **CapEx, dividends, buybacks, and M&A**.",
    },
    "section.capital.composition_rate": {
        "zh": "资本流向构成比率",
        "en": "Capital Allocation Composition Ratio",
    },
    "section.capital.diagnostics": {
        "zh": "资本分配率诊断",
        "en": "Capital Allocation Rate Diagnostics",
    },
    "section.capital.metric.capex_to_ocf": {
        "zh": "CapEx 占 OCF 比例",
        "en": "CapEx / OCF",
    },
    "section.capital.metric.capex_to_ocf_help": {
        "zh": "企业重资产程度。该比例越低，说明企业创造自由现金流的能力越强。",
        "en": "Asset intensity of the business. A lower ratio indicates stronger free cash flow generation.",
    },
    "section.capital.metric.dividend_rate": {
        "zh": "现金分红率",
        "en": "Dividend Payout Rate",
    },
    "section.capital.metric.dividend_rate_help": {
        "zh": "分配给股东的现金比例。",
        "en": "Proportion of operating cash flow distributed to shareholders as dividends.",
    },
    "section.capital.metric.buyback_rate": {
        "zh": "股份回购率",
        "en": "Share Buyback Rate",
    },
    "section.capital.metric.buyback_rate_help": {
        "zh": "利用多余现金在公开市场回购股份注销的力度。",
        "en": "Intensity of open-market share repurchases for cancellation. Higher is more aggressive return of capital.",
    },
    "section.capital.metric.ma_rate": {
        "zh": "并购与投资比率",
        "en": "M&A & Investment Rate",
    },
    "section.capital.metric.ma_rate_help": {
        "zh": "管理层通过投资或并购实现增长的力度。若该数值过高但 ROIIC 极低，可能是盲目扩张信号。",
        "en": "Management's intensity of pursuing growth through investment or M&A. If this ratio is high but ROIIC is low, it may signal wasteful empire-building.",
    },

    # ── sections: ROIC & ROIIC ───────────────────────────────────────────
    "section.roic.title": {
        "zh": "存量与增量资本配置回报率 (ROIC & ROIIC Capital Efficiency)",
        "en": "ROIC & ROIIC Capital Efficiency",
    },
    "section.roic.intro": {
        "zh": "巴菲特强调：投资人不仅要看当前的存量资本回报率 (ROIC)，更要看管理层“截留利润进行再投资”时的增量回报率 (ROIIC)。",
        "en": "Buffett emphasizes that investors should look not only at the current return on invested capital (ROIC), but also at the incremental return on capital (ROIIC) when management reinvests retained earnings.",
    },
    "section.roic.intro.bullet1": {
        "zh": "1、**ROIC（存量回报率）**：衡量目前公司已投入资本的运营效率。",
        "en": "A. **ROIC (Return on Invested Capital)**: Measures the current operational efficiency of invested capital."
    },
    "section.roic.intro.bullet2": {
        "zh": "2、**ROIIC Retained（留存再投资回报率）**：$\\Delta NOPAT / 累计留存盈余$。衡量管理层扣留盈利后，再投资的效率。",
        "en": "B. **ROIIC Retained (Incremental Return on Retained Earnings)**: $\\Delta NOPAT / Cumulative Retained Earnings$. Measures how efficiently management reinvests retained profits."
    },
    "section.roic.guidance.header": {
        "zh": "**指引**",
        "en": "**Guidance**",
    },
    "section.roic.guidance.bullet1": {
        "zh": "1、若 **ROIC 长期维持在 15% 以上**，表明公司产品或服务具备较强护城河。",
        "en": "A. If **ROIC is consistently above 15%**, the company likely possesses a durable economic moat.",
    },
    "section.roic.guidance.bullet2": {
        "zh": "2、若 **ROIIC 大幅低于 ROIC**，表明高回报的新投资机会可能正在减少，管理层应更多考虑分红与回购。",
        "en": "B. If **ROIIC is significantly below ROIC**, high-return reinvestment opportunities may be dwindling; management should consider increasing dividends or buybacks.",
    },

    # ── sections: buyback ────────────────────────────────────────────────
    "section.buyback.title": {
        "zh": "股份回购与红利分配 (Share Repurchase & Dividend Efficacy)",
        "en": "Share Repurchase & Dividend Efficacy",
    },
    "section.buyback.intro": {
        "zh": "本模块对比**实际回购成交均价**和**保守每股内在价值 (DCF)**，甄别管理层是在低估时回购创造复利，还是在高估时回购毁灭价值。",
        "en": "This module compares the **actual weighted average repurchase price** against the **conservative intrinsic value per share (DCF)** to determine whether management is buying back shares at a discount (creating compound value) or at a premium (destroying value).",
    },
    "section.buyback.detail_header": {
        "zh": "历年回购决策审计明细",
        "en": "Yearly Buyback Decision Audit Details",
    },
    "section.buyback.col.total_dividends": {
        "zh": "现金派息总额 ({currency})",
        "en": "Total Cash Dividends ({currency})",
    },
    "section.buyback.col.buyback_paid": {
        "zh": "回购现金支出 ({currency})",
        "en": "Buyback Cash Paid ({currency})",
    },
    "section.buyback.col.buyback_shares": {
        "zh": "回购股份数量（股）",
        "en": "Shares Repurchased",
    },
    "section.buyback.col.buyback_price": {
        "zh": "实际回购均价 ({currency})",
        "en": "Actual Buyback Avg Price ({currency})",
    },
    "section.buyback.col.intrinsic_value": {
        "zh": "每股估算内在价值 ({currency})",
        "en": "Est. Intrinsic Value/Share ({currency})",
    },
    "section.buyback.col.buyback_to_intrinsic": {
        "zh": "回购均价 / 内在价值",
        "en": "Buyback Price / Intrinsic Value",
    },
    "section.buyback.col.audit_rating": {
        "zh": "回购效率审计结论",
        "en": "Buyback Audit Rating",
    },

    # ── buyback ratings ──────────────────────────────────────────────────
    "buyback.rating.none": {
        "zh": "无显著回购",
        "en": "No Significant Buyback",
    },
    "buyback.rating.excellent": {
        "zh": "卓越回购（创造价值）",
        "en": "Excellent Buyback (Value-Creating)",
    },
    "buyback.rating.reasonable": {
        "zh": "合理回购（公允对价）",
        "en": "Reasonable Buyback (Fair Price)",
    },
    "buyback.rating.blind": {
        "zh": "盲目回购（摧毁价值）",
        "en": "Blind Buyback (Value-Destroying)",
    },

    # ── sections: M&A & Goodwill ─────────────────────────────────────────
    "section.ma.title": {
        "zh": "并购与商誉资本效率审计 (M&A & Goodwill Capital Efficiency)",
        "en": "M&A & Goodwill Capital Efficiency Audit",
    },
    "section.ma.intro": {
        "zh": "警惕“帝国建造者”：用高溢价并购堆砌规模，却无法让并购支出赚回资本成本。",
        "en": "Beware the \"Empire Builder\": piling up scale through high-premium M&A without earning the cost of capital on acquisition spending.",
    },
    "section.ma.intro.bullet1": {
        "zh": "1、**商誉 / 股东权益**：攀升意味着资产负债表愈发依赖并购溢价，减值风险积聚。",
        "en": "A. **Goodwill / Equity**: A rising ratio means the balance sheet is increasingly dependent on acquisition premiums. Impairment risk is accumulating."
    },
    "section.ma.intro.bullet2": {
        "zh": "2、**Acquisition ROIIC**：$\\Delta NOPAT / 累计并购支出$。衡量并购资本是否赚回资本成本，低于 WACC 即为价值毁灭。",
        "en": "B. **Acquisition ROIIC**: $\\Delta NOPAT / Cumulative M&A Spend$. Measures whether acquisition capital earns its cost of capital. Below WACC = value destruction."
    },
    "section.ma.intro.bullet3": {
        "zh": "3、**商誉增速 vs NOPAT 增速**：正值代表商誉膨胀快于利润增厚，并购未转化为真实盈利。",
        "en": "C. **Goodwill Growth vs NOPAT Growth**: A positive gap means goodwill is ballooning faster than profit growth — acquisitions are not translating into real earnings."
    },
    "section.ma.col.ma_spend": {
        "zh": "累计并购现金支出",
        "en": "Cumulative M&A Cash Spend",
    },
    "section.ma.col.ma_spend_help": {
        "zh": "审计期间管理层用于并购/投资的累计现金。",
        "en": "Cumulative cash deployed by management for M&A/investment during the audit period.",
    },
    "section.ma.col.goodwill_balance": {
        "zh": "期末商誉余额",
        "en": "Ending Goodwill Balance",
    },
    "section.ma.col.goodwill_balance_help": {
        "zh": "资产负债表上的商誉余额，占权益比越高减值风险越大。",
        "en": "Goodwill balance on the balance sheet. The higher it is relative to equity, the greater the impairment risk.",
    },
    "section.ma.col.goodwill_to_equity": {
        "zh": "商誉 / 股东权益",
        "en": "Goodwill / Equity",
    },
    "section.ma.col.goodwill_to_equity_help": {
        "zh": "商誉占股东权益比例。",
        "en": "Goodwill as a percentage of shareholders' equity.",
    },
    "section.ma.col.acquisition_roiic": {
        "zh": "Acquisition ROIIC（最新）",
        "en": "Acquisition ROIIC (Latest)",
    },
    "section.ma.col.acquisition_roiic_help": {
        "zh": "并购支出的增量资本回报率，低于 WACC 即价值毁灭。",
        "en": "Incremental return on acquisition spending. Below WACC means value destruction.",
    },
    "section.ma.warning.gw_growth": {
        "zh": "商誉增速显著超过 NOPAT 增速（差值 +{diff:.1%}），并购溢价持续堆积但未能等比例转化为经营利润，警惕未来商誉减值。",
        "en": "Goodwill growth significantly exceeds NOPAT growth (gap +{diff:.1%}). Acquisition premiums are piling up without a commensurate increase in operating profit. Watch for future goodwill impairment.",
    },
    "section.ma.success.gw_growth": {
        "zh": "NOPAT 增速超过商誉增速（差值 {diff:.1%}），并购整合见效，利润增厚快于商誉膨胀。",
        "en": "NOPAT growth exceeds goodwill growth (gap {diff:.1%}). Acquisition integration is bearing fruit — profit growth outpaces goodwill inflation.",
    },
    "section.ma.guidance.header": {
        "zh": "**指引**",
        "en": "**Guidance**",
    },
    "section.ma.guidance.bullet1": {
        "zh": "1、若 **商誉 / 股东权益 > 50%** 且 **Acquisition ROIIC < WACC**，管理层大概率在用高溢价并购毁灭价值。",
        "en": "A. If **Goodwill / Equity > 50%** and **Acquisition ROIIC < WACC**, management is likely destroying value through high-premium acquisitions.",
    },
    "section.ma.guidance.bullet2": {
        "zh": "2、若累计并购支出可观但 NOPAT 增量微弱，应质疑并购战略而非会计处理。",
        "en": "B. If cumulative M&A spend is substantial but NOPAT growth is negligible, question the M&A strategy rather than the accounting.",
    },

    # ── sections: earnings quality ───────────────────────────────────────
    "section.eq.title": {
        "zh": "盈利质量与应计项审计 (Earnings Quality & Accruals Audit)",
        "en": "Earnings Quality & Accruals Audit",
    },
    "section.eq.intro": {
        "zh": "巴菲特强调“所有者盈余”而非会计利润：真正属于股东的是现金，不是应计项。",
        "en": "Buffett emphasizes \"Owner Earnings\" over accounting profit: what truly belongs to shareholders is cash, not accruals.",
    },
    "section.eq.intro.bullet1": {
        "zh": "1、**所有者盈余 vs 净利润**：长期低于净利润，说明盈利被维持性资本支出或非现金项侵蚀。",
        "en": "A. **Owner Earnings vs Net Profit**: Persistently below net profit means earnings are being eroded by maintenance capex or non-cash items."
    },
    "section.eq.intro.bullet2": {
        "zh": "2、**FCF / 净利润**：现金转化率，低于 80% 需警惕，低于 50% 说明盈利高度依赖应计项。",
        "en": "B. **FCF / Net Profit**: Cash conversion rate. Below 80% warrants caution; below 50% means earnings are heavily dependent on accruals."
    },
    "section.eq.intro.bullet3": {
        "zh": "3、**应计项比率**：$(净利润 - 经营现金流) / 投入资本$，持续走高是会计激进的红旗信号（Sloan 异常）。",
        "en": "C. **Accruals Ratio**: $(Net Profit - Operating Cash Flow) / Invested Capital$. A persistently rising ratio is a red flag for accounting aggressiveness (the Sloan anomaly)."
    },
    "section.eq.intro.bullet4": {
        "zh": "4、**每股所有者盈余 (OEPS)**：巴菲特真正在意的“每股内在增长”口径。",
        "en": "D. **Owner Earnings Per Share (OEPS)**: The Buffett-preferred measure of intrinsic per-share growth."
    },
    "section.eq.metric.oe_to_np": {
        "zh": "所有者盈余 / 净利润",
        "en": "OE / Net Profit",
    },
    "section.eq.metric.oe_to_np_help": {
        "zh": "低于 100% 说明所有者盈余不及会计利润，盈利被维持性资本支出或非现金项侵蚀。",
        "en": "Below 100% means owner earnings lag accounting profit; earnings are eroded by maintenance capex or non-cash items.",
    },
    "section.eq.metric.fcf_to_ni": {
        "zh": "FCF / 净利润",
        "en": "FCF / Net Profit",
    },
    "section.eq.metric.fcf_to_ni_help": {
        "zh": "现金转化率，越高说明盈利含金量越足。",
        "en": "Cash conversion rate. Higher is better — more of the earnings are backed by cash.",
    },
    "section.eq.metric.accruals_ratio": {
        "zh": "应计项比率",
        "en": "Accruals Ratio",
    },
    "section.eq.metric.accruals_ratio_help": {
        "zh": "正值且走高意味着净利润超过经营现金流，会计利润含应计项偏重。",
        "en": "A positive and rising ratio means net profit exceeds operating cash flow — accounting profit is accrual-heavy.",
    },
    "section.eq.metric.oeps": {
        "zh": "每股所有者盈余 (OEPS)",
        "en": "Owner Earnings Per Share (OEPS)",
    },
    "section.eq.metric.oeps_help": {
        "zh": "巴菲特真正在意的每股内在增长口径。",
        "en": "The per-share intrinsic growth measure that Buffett truly cares about.",
    },
    "section.eq.oeps_cagr": {
        "zh": "近 {n_years} 年所有者盈余年复合增速 (OEPS CAGR)：**{cagr:.1%}**。",
        "en": "{n_years}-Year Owner Earnings CAGR: **{cagr:.1%}**.",
    },
    "section.eq.guidance.header": {
        "zh": "**指引**",
        "en": "**Guidance**",
    },
    "section.eq.guidance.bullet1": {
        "zh": "1、若 **所有者盈余长期 < 净利润**，需核查资本支出结构与非现金调整项，盈利质量可能被高估。",
        "en": "A. If **Owner Earnings persistently < Net Profit**, examine the capex structure and non-cash adjustments — earnings quality may be overstated.",
    },
    "section.eq.guidance.bullet2": {
        "zh": "2、若 **应计项比率持续为正且攀升**，结合应收账款与存货周转排查收入确认激进风险。",
        "en": "B. If the **accruals ratio is persistently positive and rising**, investigate revenue recognition aggressiveness risks in conjunction with AR and inventory turnover.",
    },

    # ── sections: checklist ──────────────────────────────────────────────
    "section.checklist.title": {
        "zh": "资本配置原则清单 (Capital Allocation Principles Checklist)",
        "en": "Capital Allocation Principles Checklist",
    },
    "section.checklist.intro": {
        "zh": "以下八条原则基于巴菲特式的资本配置检查清单，每条原则展示**客观事实数据**与**基准对比**，由系统自动计算判定状态。用户应结合行业特性与公司生命周期阶段，对未通过或警告的原则进行深入研究。",
        "en": "The following eight principles are based on a Buffett-style capital allocation checklist. Each principle presents **objective factual data** against a **benchmark**, with the status determined automatically by the system. Users should further investigate failed or warning principles in light of industry characteristics and the company's lifecycle stage.",
    },
    "section.checklist.principle_n": {
        "zh": "原则 {index}",
        "en": "Principle {index}",
    },
    "section.checklist.actual_value": {
        "zh": "实际值：",
        "en": "Actual Value: ",
    },
    "section.checklist.benchmark": {
        "zh": "基准：",
        "en": "Benchmark: ",
    },
    "section.checklist.summary_header": {
        "zh": "**汇总**：{summary}。",
        "en": "**Summary**: {summary}.",
    },
    "section.checklist.disclaimer1": {
        "zh": "本清单提供事实数据和客观判定，不构成投资建议。",
        "en": "This checklist provides factual data and objective assessments and does not constitute investment advice.",
    },
    "section.checklist.disclaimer2": {
        "zh": "请结合行业基准、竞争格局和管理层历史决策背景进行独立判断。",
        "en": "Please exercise independent judgment in light of industry benchmarks, competitive landscape, and management's historical decision-making context.",
    },

    # ── badge texts ──────────────────────────────────────────────────────
    "badge.pass": {
        "zh": "[ ✔ 通过 ]",
        "en": "[ ✔ PASS ]",
    },
    "badge.fail": {
        "zh": "[ ✘ 未通过 ]",
        "en": "[ ✘ FAIL ]",
    },
    "badge.warning": {
        "zh": "[ ! 警告 ]",
        "en": "[ ! WARNING ]",
    },
    "badge.insufficient_data": {
        "zh": "[ ? 数据不足 ]",
        "en": "[ ? INSUFFICIENT DATA ]",
    },

    # ── sections: ledger ─────────────────────────────────────────────────
    "section.ledger.title": {
        "zh": "审计模型数据底表 (Raw Data & Intermediaries)",
        "en": "Audit Model Raw Data & Intermediaries",
    },
    "section.ledger.intro": {
        "zh": "以下为系统输入参数、核心中间指标以及最终审计指标：",
        "en": "Below are the system input parameters, core intermediate indicators, and final audit metrics:",
    },
    "section.ledger.export_csv": {
        "zh": "导出完整审计表格为 CSV (Export to CSV)",
        "en": "Export Full Audit Table as CSV",
    },
    "section.ledger.duckdb_title": {
        "zh": "本地 DuckDB 缓存数据库实时诊断 (DuckDB SQL Diagnostics)",
        "en": "Local DuckDB Cache Database Live Diagnostics (DuckDB SQL Diagnostics)",
    },
    "section.ledger.duckdb_intro": {
        "zh": "本系统采用高能进程内 SQL 数据库 **DuckDB** 存储和管理从 API 抓取的数据。您可以在下方选择常用的诊断 SQL，或者直接编写自定义 SQL，实时检索并审查本地 DuckDB 缓存内容：",
        "en": "This system uses the high-performance in-process SQL database **DuckDB** to store and manage data fetched from APIs. You can select commonly used diagnostic SQL queries below, or write custom SQL to retrieve and review the local DuckDB cache content in real time:",
    },
    "section.ledger.sql_template.label": {
        "zh": "选择常用 SQL 模板",
        "en": "Select SQL Template",
    },
    "section.ledger.sql_template.latest_financials": {
        "zh": "查看最新 10 条财务底表数据",
        "en": "View Latest 10 Financial Records",
    },
    "section.ledger.sql_template.exchange_rates": {
        "zh": "查看缓存的汇率底表数据",
        "en": "View Cached Exchange Rate Data",
    },
    "section.ledger.sql_template.stock_prices": {
        "zh": "查看缓存的股价底表数据",
        "en": "View Cached Stock Price Data",
    },
    "section.ledger.sql_template.audit_inputs": {
        "zh": "查看所有成功缓存过的股票输入记录",
        "en": "View All Successfully Cached Stock Input Records",
    },
    "section.ledger.sql_template.custom": {
        "zh": "编写自定义 SQL 语句",
        "en": "Write Custom SQL",
    },
    "section.ledger.sql.editor_label": {
        "zh": "SQL 编辑器",
        "en": "SQL Editor",
    },
    "section.ledger.sql.placeholder": {
        "zh": "例如: SELECT * FROM raw_financials WHERE ticker = '0388.HK';",
        "en": "e.g.: SELECT * FROM raw_financials WHERE ticker = '0388.HK';",
    },
    "section.ledger.sql.success": {
        "zh": "SQL 执行成功",
        "en": "SQL Executed Successfully",
    },
    "section.ledger.sql.error": {
        "zh": "SQL 执行失败: {exc}",
        "en": "SQL Execution Failed: {exc}",
    },
    "section.ledger.sql.no_cache": {
        "zh": "缓存数据库 `audit_cache.db` 尚未建立。请从左侧通过 Yahoo 或 Futu 接口拉取并分析任意港股实时数据以进行初始化。",
        "en": "The cache database `audit_cache.db` has not been created yet. Please fetch and analyze any HK stock data via the Yahoo or Futu interface from the sidebar to initialize.",
    },
    "section.ledger.sql.init_error": {
        "zh": "无法初始化 DuckDB 诊断工具: {exc}",
        "en": "Unable to Initialize DuckDB Diagnostic Tool: {exc}",
    },

    # ── charts: waterfall ────────────────────────────────────────────────
    "chart.waterfall.label.ocf": {
        "zh": "经营现金流（总流入）",
        "en": "Operating Cash Flow (Inflow)",
    },
    "chart.waterfall.label.capex": {
        "zh": "资本支出 (CapEx)",
        "en": "Capital Expenditure (CapEx)",
    },
    "chart.waterfall.label.dividends": {
        "zh": "现金分红",
        "en": "Cash Dividends",
    },
    "chart.waterfall.label.buybacks": {
        "zh": "股份回购",
        "en": "Share Buybacks",
    },
    "chart.waterfall.label.ma": {
        "zh": "投资与并购",
        "en": "Investment & M&A",
    },
    "chart.waterfall.label.other": {
        "zh": "其他现金 / 债务留存",
        "en": "Other Cash / Debt Retention",
    },
    "chart.waterfall.hover": {
        "zh": "{label}<br>金额: {sign}{amount:.1f}{suffix}",
        "en": "{label}<br>Amount: {sign}{amount:.1f}{suffix}",
    },
    "chart.waterfall.title.cumulative": {
        "zh": "{start_year} - {end_year} 年累计资本分配去向瀑布图（单位：{unit_label}）",
        "en": "{start_year} - {end_year} Cumulative Capital Allocation Waterfall (Unit: {unit_label})",
    },
    "chart.waterfall.title.single": {
        "zh": "{year} 年度单年资本分配去向瀑布图（单位：{unit_label}）",
        "en": "{year} Single-Year Capital Allocation Waterfall (Unit: {unit_label})",
    },
    "chart.pie.label.capex": {
        "zh": "资本支出 (CapEx)",
        "en": "Capital Expenditure (CapEx)",
    },
    "chart.pie.label.dividends": {
        "zh": "现金分红",
        "en": "Cash Dividends",
    },
    "chart.pie.label.buybacks": {
        "zh": "股份回购",
        "en": "Share Buybacks",
    },
    "chart.pie.label.ma": {
        "zh": "投资并购",
        "en": "Investment & M&A",
    },
    "chart.pie.label.other": {
        "zh": "其他现金 / 债务留存",
        "en": "Other Cash / Debt Retention",
    },

    # ── charts: ROIC ─────────────────────────────────────────────────────
    "chart.roic.trace.roic": {
        "zh": "ROIC（存量回报率）",
        "en": "ROIC (Stock Return)",
    },
    "chart.roic.trace.roiic_retained": {
        "zh": "ROIIC Retained（{window} 年滚动增量，滞后 {lag} 年）",
        "en": "ROIIC Retained ({window}-Year Rolling, {lag}-Year Lag)",
    },
    "chart.roic.title": {
        "zh": "ROIC 与 ROIIC（留存盈余视角）趋势",
        "en": "ROIC vs. ROIIC (Retained Earnings Perspective) Trend",
    },
    "chart.roic.xaxis": {
        "zh": "年份",
        "en": "Year",
    },
    "chart.roic.yaxis": {
        "zh": "回报率",
        "en": "Return",
    },

    # ── charts: buyback ──────────────────────────────────────────────────
    "chart.buyback.trace.intrinsic": {
        "zh": "保守每股内在价值（折算为市场币种）",
        "en": "Conservative Intrinsic Value/Share (Market Currency)",
    },
    "chart.buyback.trace.avg_price": {
        "zh": "年平均交易股价",
        "en": "Annual Average Trading Price",
    },
    "chart.buyback.trace.buyback_price": {
        "zh": "实际股份回购均价",
        "en": "Actual Buyback Avg Price",
    },
    "chart.buyback.title": {
        "zh": "每股内在价值（估值锚）vs. 年度均价 vs. 实际回购成交价",
        "en": "Intrinsic Value/Share (Valuation Anchor) vs. Avg Price vs. Actual Buyback Price",
    },
    "chart.buyback.yaxis": {
        "zh": "价格 ({currency})",
        "en": "Price ({currency})",
    },

    # ── charts: M&A / Goodwill ───────────────────────────────────────────
    "chart.ma.trace.goodwill_to_equity": {
        "zh": "商誉 / 股东权益",
        "en": "Goodwill / Equity",
    },
    "chart.ma.trace.ma_spend": {
        "zh": "并购现金支出 ({suffix})",
        "en": "M&A Cash Spend ({suffix})",
    },
    "chart.ma.trace.acquisition_roiic": {
        "zh": "Acquisition ROIIC（{window} 年滚动，滞后 {lag} 年）",
        "en": "Acquisition ROIIC ({window}-Year Rolling, {lag}-Year Lag)",
    },
    "chart.ma.title": {
        "zh": "商誉占比、并购支出与并购资本回报率",
        "en": "Goodwill Ratio, M&A Spend & Acquisition ROIIC",
    },
    "chart.ma.yaxis": {
        "zh": "回报率 / 占比",
        "en": "Return / Ratio",
    },
    "chart.ma.yaxis2": {
        "zh": "并购支出",
        "en": "M&A Spend",
    },

    # ── charts: earnings quality ─────────────────────────────────────────
    "chart.eq.trace.net_profit": {
        "zh": "净利润",
        "en": "Net Profit",
    },
    "chart.eq.trace.owner_earnings": {
        "zh": "所有者盈余",
        "en": "Owner Earnings",
    },
    "chart.eq.trace.fcf": {
        "zh": "自由现金流",
        "en": "Free Cash Flow",
    },
    "chart.eq.trace.accruals_ratio": {
        "zh": "应计项比率",
        "en": "Accruals Ratio",
    },
    "chart.eq.title": {
        "zh": "净利润 vs 所有者盈余 vs 自由现金流（含应计项比率）",
        "en": "Net Profit vs Owner Earnings vs FCF (with Accruals Ratio)",
    },
    "chart.eq.yaxis": {
        "zh": "金额 ({suffix})",
        "en": "Amount ({suffix})",
    },
    "chart.eq.yaxis2": {
        "zh": "应计项比率",
        "en": "Accruals Ratio",
    },

    # ── chart generic ────────────────────────────────────────────────────
    "chart.xaxis.year": {
        "zh": "年份",
        "en": "Year",
    },
    "chart.unit.billions": {
        "zh": "十亿",
        "en": "Billions",
    },
    "chart.unit.millions": {
        "zh": "百万",
        "en": "Millions",
    },

    # =====================================================================
    #  CHECKLIST PRINCIPLE TITLES
    # =====================================================================
    "checklist.p1.title": {
        "zh": "资本回报率是否高于资本成本？",
        "en": "Is ROIC above the cost of capital?",
    },
    "checklist.p2.title": {
        "zh": "留存利润是否被高效再投资？",
        "en": "Is retained profit reinvested efficiently?",
    },
    "checklist.p3.title": {
        "zh": "每 $1 留存是否创造 >$1 市值？",
        "en": "Does every $1 retained create >$1 market value?",
    },
    "checklist.p4.title": {
        "zh": "回购是否具有纪律性（低于内在价值）？",
        "en": "Are buybacks disciplined (below intrinsic value)?",
    },
    "checklist.p5.title": {
        "zh": "分红是否被自由现金流覆盖？",
        "en": "Are dividends covered by free cash flow?",
    },
    "checklist.p6.title": {
        "zh": "资本效率趋势是否改善？",
        "en": "Is the capital efficiency trend improving?",
    },
    "checklist.p7.title": {
        "zh": "并购是否创造高于资本成本的价值？",
        "en": "Do acquisitions create value above the cost of capital?",
    },
    "checklist.p8.title": {
        "zh": "盈利质量是否健康（现金转化）？",
        "en": "Is earnings quality healthy (cash-backed)?",
    },

    # =====================================================================
    #  CHECKLIST P1: ROIC vs WACC
    # =====================================================================
    "checklist.p1.value.negative_ic": {
        "zh": "极高 (Negative IC)",
        "en": "Extremely High (Negative IC)",
    },
    "checklist.p1.benchmark.wacc_spread": {
        "zh": "WACC {wacc:.1%}（利差 {spread:+.1%}）",
        "en": "WACC {wacc:.1%} (Spread {spread:+.1%})",
    },
    "checklist.p1.desc.insufficient": {
        "zh": "ROIC 数据不足，无法判断是否创造价值。",
        "en": "Insufficient ROIC data to determine whether value is being created.",
    },
    "checklist.p1.desc.money_printer": {
        "zh": "公司近 5 年平均投入资本为负或零，且税后经营利润 (NOPAT) 持续为正。这意味着公司不需要股东与债权人投入额外本金，便能靠经营性负债与丰沛现金流运转（零/负投入资本扩张），属于商业壁垒极高的特许经营“印钞机”型公司，其资本效率极高，回报率视为无限大！",
        "en": "The company's 5-year average invested capital is negative or zero, while NOPAT remains consistently positive. This means the company does not require additional capital from shareholders or creditors — it can operate on operational liabilities and abundant cash flow (zero/negative invested capital expansion). This is a franchise \"money printer\" with extremely high business barriers, and its capital efficiency is treated as infinite!",
    },
    "checklist.p1.desc.pass": {
        "zh": "近 5 年平均 ROIC {avg_roic:.1%} 高于 WACC {wacc:.1%}，利差 +{spread:.1%}，公司持续创造经济价值。",
        "en": "5-year average ROIC of {avg_roic:.1%} exceeds WACC of {wacc:.1%}, with a spread of +{spread:.1%}. The company is consistently creating economic value.",
    },
    "checklist.p1.desc.fail": {
        "zh": "近 5 年平均 ROIC {avg_roic:.1%} 低于 WACC {wacc:.1%}，利差 {spread:.1%}，公司在毁灭股东价值。",
        "en": "5-year average ROIC of {avg_roic:.1%} is below WACC of {wacc:.1%}, with a spread of {spread:.1%}. The company is destroying shareholder value.",
    },

    # =====================================================================
    #  CHECKLIST P2: ROIIC vs ROIC
    # =====================================================================
    "checklist.p2.benchmark.negative_ic": {
        "zh": "ROIC 极高 (Negative IC)",
        "en": "ROIC Extremely High (Negative IC)",
    },
    "checklist.p2.value.capital_light": {
        "zh": "极高 (Capital-Light)",
        "en": "Extremely High (Capital-Light)",
    },
    "checklist.p2.desc.insufficient": {
        "zh": "ROIIC 数据不足，无法评估增量再投资效率。",
        "en": "Insufficient ROIIC data to assess incremental reinvestment efficiency.",
    },
    "checklist.p2.desc.capital_light": {
        "zh": "公司在过去 {window} 年累计未留下任何盈余（可能全部用于分红与回购），但税后经营利润 (NOPAT) 仍然实现了增长。这代表了极其优异的“零资本 / 轻资产扩张模式”，边际增量再投资效率极高！",
        "en": "The company retained no earnings over the past {window} years (likely fully distributed as dividends and buybacks), yet NOPAT still grew. This represents an exceptional \"zero-capital / asset-light expansion\" model with extremely high marginal reinvestment efficiency!",
    },
    "checklist.p2.desc.inf_roic_pass": {
        "zh": "虽然因存量投入资本为负使得存量 ROIC 视为无限大，但公司增量再投资回报率 (ROIIC) 达到 {roiic:.1%}，远高于 WACC {wacc:.1%}，管理层的增量资金部署依然极其高效。",
        "en": "Although stock ROIC is treated as infinite due to negative invested capital, the company's incremental ROIIC reaches {roiic:.1%}, far above the WACC of {wacc:.1%}. Management's incremental capital deployment remains highly efficient.",
    },
    "checklist.p2.desc.inf_roic_fail": {
        "zh": "虽然存量 ROIC 视为无限大，但公司增量再投资回报率 (ROIIC) 仅为 {roiic:.1%}，低于资本成本 WACC {wacc:.1%}，说明留存利润的边际使用效率低下，应加大分红或回购。",
        "en": "Although stock ROIC is treated as infinite, the company's incremental ROIIC is only {roiic:.1%}, below the cost of capital (WACC {wacc:.1%}). The marginal efficiency of retained earnings is poor — the company should increase dividends or buybacks.",
    },
    "checklist.p2.desc.ge_avg": {
        "zh": "ROIIC {roiic:.1%} ≥ ROIC {roic:.1%}，增量投资回报不低于存量资本，管理层仍能找到高回报投资机会。",
        "en": "ROIIC of {roiic:.1%} ≥ ROIC of {roic:.1%}. Incremental returns are at least as good as existing capital returns — management is still finding high-return investment opportunities.",
    },
    "checklist.p2.desc.ge_wacc": {
        "zh": "ROIIC {roiic:.1%} < ROIC {roic:.1%}，边际效率递减，但仍高于 WACC {wacc:.1%}，再投资仍在创造价值但护城河可能收窄。",
        "en": "ROIIC of {roiic:.1%} < ROIC of {roic:.1%}. Marginal efficiency is declining, but still above WACC of {wacc:.1%}. Reinvestment is still creating value, though the moat may be narrowing.",
    },
    "checklist.p2.desc.lt_wacc": {
        "zh": "ROIIC {roiic:.1%} < WACC {wacc:.1%}，增量投资回报低于资本成本，管理层在低效扩张，应转向分红或回购。",
        "en": "ROIIC of {roiic:.1%} < WACC of {wacc:.1%}. Incremental returns are below the cost of capital. Management is expanding inefficiently and should pivot to dividends or buybacks.",
    },

    # =====================================================================
    #  CHECKLIST P3: One-Dollar Rule
    # =====================================================================
    "checklist.p3.desc.insufficient": {
        "zh": "一美元原则数据不足，无法评估市值创造效率。",
        "en": "Insufficient one-dollar-rule data to assess market value creation efficiency.",
    },
    "checklist.p3.desc.pass": {
        "zh": "每留存 $1 创造了 ${value:.2f} 市值，市场对管理层的资本配置投出信任票。",
        "en": "Every $1 retained created ${value:.2f} in market value. The market votes confidence in management's capital allocation.",
    },
    "checklist.p3.desc.warning": {
        "zh": "每留存 $1 仅创造 ${value:.2f} 市值，留存利润的市场认可度不足，资本配置效率存疑。",
        "en": "Every $1 retained created only ${value:.2f} in market value. Market recognition of retained earnings is inadequate — capital allocation efficiency is questionable.",
    },
    "checklist.p3.desc.fail": {
        "zh": "每留存 $1 仅创造 ${value:.2f} 市值，管理层截留利润却未能转化为市场价值，严重摧毁股东财富。",
        "en": "Every $1 retained created only ${value:.2f} in market value. Management is hoarding profits without converting them into market value — severely destroying shareholder wealth.",
    },

    # =====================================================================
    #  CHECKLIST P4: Buyback Discipline
    # =====================================================================
    "checklist.p4.benchmark.le_085": {
        "zh": "≤ 0.85x 内在价值",
        "en": "≤ 0.85x Intrinsic Value",
    },
    "checklist.p4.value.ratio": {
        "zh": "{ratio:.2f}x 内在价值",
        "en": "{ratio:.2f}x Intrinsic Value",
    },
    "checklist.p4.desc.insufficient": {
        "zh": "审计期间无显著回购记录，无法评估回购纪律。",
        "en": "No significant buyback activity during the audit period. Unable to assess buyback discipline.",
    },
    "checklist.p4.desc.pass": {
        "zh": "加权回购均价为内在价值的 {ratio:.2f}x，管理层在低估时回购，实实在在地增厚长期股东权益。",
        "en": "Weighted average buyback price is {ratio:.2f}x intrinsic value. Management is buying back shares at a discount, genuinely enhancing long-term shareholder equity.",
    },
    "checklist.p4.desc.warning": {
        "zh": "加权回购均价为内在价值的 {ratio:.2f}x，回购价格接近公允价值，未造成重大价值损失但也未创造显著超额回报。",
        "en": "Weighted average buyback price is {ratio:.2f}x intrinsic value. The buyback price is near fair value — no significant value destruction, but no meaningful excess returns either.",
    },
    "checklist.p4.desc.fail": {
        "zh": "加权回购均价为内在价值的 {ratio:.2f}x，管理层在高估时回购，用真金白银补贴离场股东，损害长期持有者利益。",
        "en": "Weighted average buyback price is {ratio:.2f}x intrinsic value. Management is buying back at a premium, using real cash to subsidize exiting shareholders at the expense of long-term holders.",
    },

    # =====================================================================
    #  CHECKLIST P5: FCF Coverage
    # =====================================================================
    "checklist.p5.benchmark": {
        "zh": "FCF 派发率 ≤ 100%",
        "en": "FCF Payout Ratio ≤ 100%",
    },
    "checklist.p5.value.neg_fcf": {
        "zh": "N/A（FCF 为负）",
        "en": "N/A (Negative FCF)",
    },
    "checklist.p5.desc.insufficient": {
        "zh": "审计期间未进行现金分红或回购，无法评估分红可持续性。",
        "en": "No cash dividends or buybacks during the audit period. Unable to assess dividend sustainability.",
    },
    "checklist.p5.desc.neg_fcf": {
        "zh": "累计自由现金流为负，公司在举债分红或回购，不可持续。",
        "en": "Cumulative free cash flow is negative. The company is borrowing to fund dividends or buybacks — this is unsustainable.",
    },
    "checklist.p5.desc.pass": {
        "zh": "FCF 派发率 {ratio:.1%}，分红与回购完全被自由现金流覆盖，可持续。",
        "en": "FCF payout ratio of {ratio:.1%}. Dividends and buybacks are fully covered by free cash flow — sustainable.",
    },
    "checklist.p5.desc.warning": {
        "zh": "FCF 派发率 {ratio:.1%}，分红略超自由现金流，长期可能需举债维持，需关注。",
        "en": "FCF payout ratio of {ratio:.1%}. Distributions slightly exceed free cash flow — may require borrowing to sustain in the long term. Monitor closely.",
    },
    "checklist.p5.desc.fail": {
        "zh": "FCF 派发率 {ratio:.1%}，分红大幅超出自由现金流，不可持续，存在毁灭价值风险。",
        "en": "FCF payout ratio of {ratio:.1%}. Distributions significantly exceed free cash flow — unsustainable and poses a value-destruction risk.",
    },

    # =====================================================================
    #  CHECKLIST P6: ROIC Trend
    # =====================================================================
    "checklist.p6.benchmark.trend": {
        "zh": "ROIC 趋势",
        "en": "ROIC Trend",
    },
    "checklist.p6.value.sustained_inf": {
        "zh": "持续极高 (Negative IC)",
        "en": "Sustained Extremely High (Negative IC)",
    },
    "checklist.p6.benchmark.excellent": {
        "zh": "持续优秀",
        "en": "Sustained Excellence",
    },
    "checklist.p6.value.leap": {
        "zh": "{first_roic:.1%} → 极高",
        "en": "{first_roic:.1%} → Extremely High",
    },
    "checklist.p6.benchmark.improving": {
        "zh": "持续改善",
        "en": "Continuously Improving",
    },
    "checklist.p6.value.slip": {
        "zh": "极高 → {last_roic:.1%}",
        "en": "Extremely High → {last_roic:.1%}",
    },
    "checklist.p6.benchmark.advantage": {
        "zh": "保持优势",
        "en": "Maintaining Advantage",
    },
    "checklist.p6.benchmark.trend_val": {
        "zh": "趋势 {trend:+.1%}",
        "en": "Trend {trend:+.1%}",
    },
    "checklist.p6.desc.insufficient": {
        "zh": "ROIC 数据不足，无法判断趋势方向。",
        "en": "Insufficient ROIC data to determine the trend direction.",
    },
    "checklist.p6.desc.insufficient_points": {
        "zh": "ROIC 数据点不足（需至少 2 年），无法判断趋势。",
        "en": "Insufficient ROIC data points (at least 2 years required) to determine the trend.",
    },
    "checklist.p6.desc.sustained_inf": {
        "zh": "公司近 {n_years} 年起始与期末的存量 ROIC 均视为无限大（持续处于负投入资本运转的“印钞机”状态），经营壁垒和资信占资优势极其稳固，资本效率卓越且稳定。",
        "en": "The company's ROIC has been treated as infinite throughout the past {n_years} years (continuously operating in a \"money printer\" state with negative invested capital). Its business moat and credit-based funding advantage are extremely solid — capital efficiency is outstanding and stable.",
    },
    "checklist.p6.desc.leap": {
        "zh": "公司近 {n_years} 年 ROIC 从起始年份的 {first_roic:.1%} 跨越式跃升至期末年份的无限大（成功转型为零/负投入资本运转的印钞机状态），商业模式和资信壁垒呈现爆发式改善。",
        "en": "ROIC leapt from {first_roic:.1%} at the start to infinity at the end over the past {n_years} years (successfully transforming into a zero/negative invested capital money printer). The business model and credit barrier have improved explosively.",
    },
    "checklist.p6.desc.slip": {
        "zh": "公司近 {n_years} 年 ROIC 从起始年份的无限大（负投入资本印钞机状态）跌落至期末年份的 {last_roic:.1%}，说明公司的负投入资本红利有所收窄，或商业渠道优势发生松动，护城河出现侵蚀迹象。",
        "en": "ROIC has fallen from infinity (negative invested capital money printer) at the start to {last_roic:.1%} at the end over the past {n_years} years. The company's negative-invested-capital advantage is shrinking, or its commercial channel advantage is weakening — signs of moat erosion.",
    },
    "checklist.p6.desc.improve": {
        "zh": "近 {n_years} 年 ROIC 从 {first_roic:.1%} 提升至 {last_roic:.1%}（+{trend:.1%}），护城河持续加固。",
        "en": "ROIC improved from {first_roic:.1%} to {last_roic:.1%} over the past {n_years} years (+{trend:.1%}). The moat continues to strengthen.",
    },
    "checklist.p6.desc.stable": {
        "zh": "近 {n_years} 年 ROIC 从 {first_roic:.1%} 变动至 {last_roic:.1%}（{trend:+.1%}），基本稳定但需关注。",
        "en": "ROIC moved from {first_roic:.1%} to {last_roic:.1%} over the past {n_years} years ({trend:+.1%}). Generally stable but warrants attention.",
    },
    "checklist.p6.desc.decline": {
        "zh": "近 {n_years} 年 ROIC 从 {first_roic:.1%} 下滑至 {last_roic:.1%}（{trend:.1%}），护城河明显侵蚀。",
        "en": "ROIC declined from {first_roic:.1%} to {last_roic:.1%} over the past {n_years} years ({trend:.1%}). The moat is clearly eroding.",
    },

    # =====================================================================
    #  CHECKLIST P7: Acquisition ROIIC
    # =====================================================================
    "checklist.p7.benchmark.wacc": {
        "zh": "WACC {wacc:.1%}",
        "en": "WACC {wacc:.1%}",
    },
    "checklist.p7.benchmark.inf_roic": {
        "zh": "ROIC 极高 / WACC {wacc:.1%}",
        "en": "ROIC Extremely High / WACC {wacc:.1%}",
    },
    "checklist.p7.value.excellent": {
        "zh": "极高",
        "en": "Extremely High",
    },
    "checklist.p7.desc.insufficient": {
        "zh": "审计期间无显著并购支出，或 Acquisition ROIIC 数据不足，无法评估并购资本效率。",
        "en": "No significant M&A spending during the audit period, or insufficient Acquisition ROIIC data to assess M&A capital efficiency.",
    },
    "checklist.p7.desc.excellent": {
        "zh": "Acquisition ROIIC 极为卓越（无限大），并购支出高效地创造了无需本金投入的额外税后经营利润！",
        "en": "Acquisition ROIIC is exceptionally high (infinite). M&A spending has efficiently created additional NOPAT without requiring additional invested capital!",
    },
    "checklist.p7.desc.inf_roic_pass": {
        "zh": "虽然因存量投入资本为负使得存量 ROIC 视为无限大，但公司并购增量回报率 (Acquisition ROIIC) 达到 {roiic:.1%}，高于 WACC {wacc:.1%}，管理层的外延并购资金配置极其成功。",
        "en": "Although stock ROIC is treated as infinite due to negative invested capital, Acquisition ROIIC reaches {roiic:.1%}, above WACC of {wacc:.1%}. Management's M&A capital deployment has been extremely successful.",
    },
    "checklist.p7.desc.inf_roic_fail": {
        "zh": "虽然存量 ROIC 视为无限大，但公司并购增量回报率 (Acquisition ROIIC) 仅为 {roiic:.1%}，低于 WACC {wacc:.1%}，表明外延并购在低效消耗资金，未能跑赢基本资金成本。",
        "en": "Although stock ROIC is treated as infinite, Acquisition ROIIC is only {roiic:.1%}, below WACC of {wacc:.1%}. This indicates M&A is inefficiently consuming capital and failing to beat the basic cost of capital.",
    },
    "checklist.p7.desc.ge_avg": {
        "zh": "Acquisition ROIIC {roiic:.1%} ≥ ROIC {roic:.1%}，并购支出带来的增量回报不低于存量资本，管理层在为股东创造价值。",
        "en": "Acquisition ROIIC of {roiic:.1%} ≥ ROIC of {roic:.1%}. Incremental returns from M&A are at least as good as existing capital returns — management is creating shareholder value.",
    },
    "checklist.p7.desc.ge_wacc": {
        "zh": "Acquisition ROIIC {roiic:.1%} < ROIC {roic:.1%}，并购回报边际递减但仍高于 WACC {wacc:.1%}，并购尚在创造价值但溢价纪律需警惕。",
        "en": "Acquisition ROIIC of {roiic:.1%} < ROIC of {roic:.1%}. M&A returns are marginally declining but still above WACC of {wacc:.1%}. M&A is still creating value, but premium discipline needs monitoring.",
    },
    "checklist.p7.desc.lt_wacc": {
        "zh": "Acquisition ROIIC {roiic:.1%} < WACC {wacc:.1%}，并购支出回报低于资本成本，管理层疑似正在毁灭股东价值。",
        "en": "Acquisition ROIIC of {roiic:.1%} < WACC of {wacc:.1%}. M&A returns are below the cost of capital. Management appears to be destroying shareholder value.",
    },

    # =====================================================================
    #  CHECKLIST P8: Earnings Quality
    # =====================================================================
    "checklist.p8.benchmark": {
        "zh": "FCF / 净利润 ≥ 80%",
        "en": "FCF / Net Profit ≥ 80%",
    },
    "checklist.p8.desc.insufficient": {
        "zh": "审计期间无正净利润年度，无法评估盈利的现金支撑度。",
        "en": "No positive net profit years during the audit period. Unable to assess cash backing of earnings.",
    },
    "checklist.p8.desc.pass": {
        "zh": "近 {n_years} 年平均 FCF/净利润 {ratio:.1%}，盈利高度由自由现金流支撑，会计利润含金量充足。",
        "en": "{n_years}-year average FCF/Net Profit of {ratio:.1%}. Earnings are strongly backed by free cash flow — accounting profit quality is solid.",
    },
    "checklist.p8.desc.warning": {
        "zh": "近 {n_years} 年平均 FCF/净利润 {ratio:.1%}，现金转化偏低，应计项偏重，盈利质量需结合应收与存货进一步核查。",
        "en": "{n_years}-year average FCF/Net Profit of {ratio:.1%}. Cash conversion is on the low side with a bias towards accruals — earnings quality warrants further investigation against AR and inventory.",
    },
    "checklist.p8.desc.fail": {
        "zh": "近 {n_years} 年平均 FCF/净利润 {ratio:.1%}，自由现金流远低于会计利润，盈利高度依赖应计项，质量存疑。",
        "en": "{n_years}-year average FCF/Net Profit of {ratio:.1%}. Free cash flow is far below accounting profit — earnings are heavily dependent on accruals and quality is questionable.",
    },

    # ── checklist summary (callable) ─────────────────────────────────────
    "checklist.summary": {
        "zh": lambda pass_count, total, warning_count, fail_count, insufficient_count:
            f"{pass_count}/{total} 原则通过"
            + (f"，{warning_count} 条警告" if warning_count > 0 else "")
            + (f"，{fail_count} 条未通过" if fail_count > 0 else "")
            + (f"，{insufficient_count} 条数据不足" if insufficient_count > 0 else ""),
        "en": lambda pass_count, total, warning_count, fail_count, insufficient_count:
            f"{pass_count}/{total} principles passed"
            + (f", {warning_count} warning(s)" if warning_count > 0 else "")
            + (f", {fail_count} failed" if fail_count > 0 else "")
            + (f", {insufficient_count} insufficient data" if insufficient_count > 0 else ""),
    },

    # ── error messages ──────────────────────────────────────────────────
    "error.wacc_le_terminal": {
        "zh": "折现率 WACC 必须大于永续增长率。",
        "en": "WACC must be greater than the terminal growth rate.",
    },
}
