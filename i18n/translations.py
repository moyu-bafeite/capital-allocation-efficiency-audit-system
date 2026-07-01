TRANSLATIONS = {
    # ── app.py ──────────────────────────────────────────────────────────
    "app.title": {
        "zh": "資本配置審計系統",
        "en": "Capital Allocation Audit System",
    },
    "app.error.audit_failed": {
        "zh": "❌ 審計模型運行失敗：{exc}",
        "en": "❌ Audit model execution failed: {exc}",
    },
    "app.nav_caption": {
        "zh": "審計維度",
        "en": "Audit Dimension",
    },

    # ── sidebar ─────────────────────────────────────────────────────────
    "sidebar.language": {
        "zh": "語言",
        "en": "Language",
    },
    "sidebar.toolbox": {
        "zh": "工具箱",
        "en": "Toolbox",
    },
    "sidebar.download_template": {
        "zh": "下載 JSON 財報輸入模板",
        "en": "Download JSON Financial Input Template",
    },
    "sidebar.pdf_export_header": {
        "zh": "PDF 報告導出",
        "en": "Export PDF Report",
    },
    "sidebar.pdf_export_button": {
        "zh": "生成 PDF 審計報告",
        "en": "Generate PDF Audit Report",
    },
    "sidebar.pdf_export_building": {
        "zh": "正在生成 PDF 報告，含圖表渲染，請稍候...",
        "en": "Building PDF report with charts, please wait...",
    },
    "sidebar.pdf_download": {
        "zh": "下載 PDF 報告",
        "en": "Download PDF Report",
    },
    "sidebar.pdf_export_dep_error": {
        "zh": "缺少 PDF 生成依賴：{exc}。請運行 `pip install weasyprint kaleido` 並安裝系統庫（macOS: `brew install cairo pango gdk-pixbuf libffi`）。",
        "en": "Missing PDF generation dependency: {exc}. Run `pip install weasyprint kaleido` and install system libs (macOS: `brew install cairo pango gdk-pixbuf libffi`).",
    },
    "sidebar.pdf_export_error": {
        "zh": "PDF 生成失敗：{exc}",
        "en": "PDF generation failed: {exc}",
    },
    "sidebar.report_export_header": {
        "zh": "審計報告導出",
        "en": "Audit Report Export",
    },
    "sidebar.report_format.label": {
        "zh": "報告格式",
        "en": "Report Format",
    },
    "sidebar.report_format.html": {
        "zh": "HTML · 交互式 (零依賴，推薦)",
        "en": "HTML · Interactive (Zero Deps, Recommended)",
    },
    "sidebar.report_format.pdf": {
        "zh": "PDF · 固定排版 (需系統依賴)",
        "en": "PDF · Fixed Layout (System Deps)",
    },
    "sidebar.report_format.help": {
        "zh": "HTML 報告含可交互圖表，無需額外系統依賴，適合屏幕瀏覽與分享；PDF 報告排版固定，適合打印存檔，但需安裝 cairo/pango 系統庫。",
        "en": "HTML report has interactive charts and no system dependencies, suited for screen viewing and sharing; PDF report has fixed layout for printing/archiving, but requires cairo/pango system libraries.",
    },
    "sidebar.report_export_button": {
        "zh": "生成審計報告",
        "en": "Generate Audit Report",
    },
    "sidebar.report_export_building": {
        "zh": "正在生成審計報告，含圖表渲染，請稍候...",
        "en": "Building audit report with charts, please wait...",
    },
    "sidebar.report_download": {
        "zh": "下載審計報告",
        "en": "Download Audit Report",
    },
    "sidebar.report_export_dep_error": {
        "zh": "缺少報告生成依賴：{exc}。PDF 路徑需運行 `pip install weasyprint kaleido` 並安裝系統庫（macOS: `brew install cairo pango gdk-pixbuf libffi`）；HTML 路徑無需額外依賴。",
        "en": "Missing report generation dependency: {exc}. PDF path requires `pip install weasyprint kaleido` plus system libs (macOS: `brew install cairo pango gdk-pixbuf libffi`); HTML path needs no extra deps.",
    },
    "sidebar.report_export_error": {
        "zh": "報告生成失敗：{exc}",
        "en": "Report generation failed: {exc}",
    },
    "sidebar.template.company_name": {
        "zh": "示例港股公司",
        "en": "Sample HK Listed Company",
    },
    "sidebar.params_header": {
        "zh": "審計與估值模型參數",
        "en": "Audit & Valuation Model Parameters",
    },
    "sidebar.params.section1": {
        "zh": "1. 維持性資本支出",
        "en": "1. Maintenance Capital Expenditure",
    },
    "sidebar.params.maintenance_capex_ratio": {
        "zh": "維持性 CapEx 佔總資本開支比例",
        "en": "Maintenance CapEx as % of Total CapEx",
    },
    "sidebar.params.maintenance_capex_help": {
        "zh": "巴菲特定義“所有者盈餘”時需扣除維持目前業務所需資本開支 (Maintenance CapEx)。財報中一般未披露，50% 為保守默認估算值。",
        "en": "Buffett defines \"Owner Earnings\" by deducting the capex needed to maintain the current business. Since financial statements rarely disclose this figure, 50% is a conservative default estimate.",
    },
    "sidebar.params.section2": {
        "zh": "2. ROIIC 滾動窗口與滯後參數",
        "en": "2. ROIIC Rolling Window & Lag Parameters",
    },
    "sidebar.params.roiic_window_1": {
        "zh": "ROIIC 短窗口年數",
        "en": "ROIIC Short Window (Years)",
    },
    "sidebar.params.roiic_window_1_help": {
        "zh": "用於生成第一個 ROIIC / ROIIC Retained 滾動窗口，默認 3 年。",
        "en": "Used to generate the first ROIIC / ROIIC Retained rolling window. Default: 3 years.",
    },
    "sidebar.params.roiic_window_2": {
        "zh": "ROIIC 長窗口年數",
        "en": "ROIIC Long Window (Years)",
    },
    "sidebar.params.roiic_window_2_help": {
        "zh": "用於生成第二個 ROIIC / ROIIC Retained 滾動窗口，默認 5 年。",
        "en": "Used to generate the second ROIIC / ROIIC Retained rolling window. Default: 5 years.",
    },
    "sidebar.params.roiic_retained_lag": {
        "zh": "ROIIC Retained 留存收益滯後年數",
        "en": "ROIIC Retained Lag (Years)",
    },
    "sidebar.params.roiic_retained_lag_help": {
        "zh": "lag=1 時，計算 T+3 的 3 年 ROIIC Retained 會使用 T、T+1、T+2 的累計留存收益。",
        "en": "When lag=1, a 3-Year ROIIC Retained for year T+3 uses cumulative retained earnings from T, T+1, and T+2.",
    },
    "sidebar.params.section3": {
        "zh": "3. 兩階段 DCF 估值模型參數",
        "en": "3. Two-Stage DCF Valuation Parameters",
    },
    "sidebar.params.wacc": {
        "zh": "折現率 (WACC / 機會成本)",
        "en": "Discount Rate (WACC / Opportunity Cost)",
    },
    "sidebar.params.growth_stage_1": {
        "zh": "第一階段增長率（前 5 年）",
        "en": "Stage 1 Growth Rate (First 5 Years)",
    },
    "sidebar.params.growth_stage_2": {
        "zh": "第二階段增長率（後 5 年）",
        "en": "Stage 2 Growth Rate (Next 5 Years)",
    },
    "sidebar.params.terminal_growth": {
        "zh": "永續增長率 (Terminal Growth)",
        "en": "Terminal Growth Rate",
    },
    "sidebar.error.wacc_le_terminal": {
        "zh": "折現率 WACC 必須大於永續增長率。",
        "en": "WACC must be greater than the terminal growth rate.",
    },
    "sidebar.data_source_header": {
        "zh": "數據源選擇與載入",
        "en": "Data Source Selection & Loading",
    },
    "sidebar.data_source.label": {
        "zh": "選擇審計標的",
        "en": "Select Audit Target",
    },
    "sidebar.data_source.futu": {
        "zh": "從 Futu OpenD 實時拉取",
        "en": "Fetch Live from Futu OpenD",
    },
    "sidebar.data_source.upload": {
        "zh": "上傳自定義 JSON 數據文件",
        "en": "Upload Custom JSON Data File",
    },
    "sidebar.upload.label": {
        "zh": "上傳結構化 JSON 財報文件",
        "en": "Upload Structured JSON Financial File",
    },
    "sidebar.upload.success": {
        "zh": "上傳成功",
        "en": "Upload Successful",
    },
    "sidebar.upload.parse_error": {
        "zh": "解析/校驗 JSON 失敗: {exc}",
        "en": "JSON Parse/Validation Failed: {exc}",
    },
    "sidebar.upload.prompt": {
        "zh": "請在側邊欄上傳 JSON 財報文件啓動審計系統。",
        "en": "Please upload a JSON financial file in the sidebar to start the audit system.",
    },
    "sidebar.futu.ticker_input": {
        "zh": "輸入港股代碼",
        "en": "Enter HK Stock Code",
    },
    "sidebar.futu.ticker_help": {
        "zh": "例如: 0388.HK, 9988.HK 或 HK.00388",
        "en": "e.g.: 0388.HK, 9988.HK or HK.00388",
    },
    "sidebar.futu.year_range": {
        "zh": "選擇財報審計年份區間",
        "en": "Select Financial Year Range",
    },
    "sidebar.futu.force_refresh": {
        "zh": "強制刷新本地數據庫緩存",
        "en": "Force Refresh Local Database Cache",
    },
    "sidebar.futu.fetch_btn": {
        "zh": "開始拉取並審計",
        "en": "Fetch & Audit",
    },
    "sidebar.futu.loading": {
        "zh": "正在加載財報數據...",
        "en": "Loading financial data...",
    },
    "sidebar.futu.load_success": {
        "zh": "成功加載 {ticker} ({year_start}-{year_end})",
        "en": "Successfully loaded {ticker} ({year_start}-{year_end})",
    },
    "sidebar.futu.load_error": {
        "zh": "數據加載失敗：{exc}",
        "en": "Data loading failed: {exc}",
    },
    "sidebar.futu.start_prompt": {
        "zh": "請在側邊欄調整參數，並點擊【開始拉取並審計】按鈕開始。",
        "en": "Please adjust parameters in the sidebar and click the [Fetch & Audit] button to start.",
    },

    # ── sections: navigation ─────────────────────────────────────────────
    "section.nav.label": {
        "zh": "選擇審計分析維度",
        "en": "Select Audit Dimension",
    },
    "section.nav.capital_allocation": {
        "zh": "累計資本流向 · Capital Allocation",
        "en": "Capital Allocation · 累计资本流向",
    },
    "section.nav.roic_roiic": {
        "zh": "存量與增量回報 · ROIC & ROIIC",
        "en": "ROIC & ROIIC · 存量与增量回报",
    },
    "section.nav.buyback": {
        "zh": "股東回報分配 · Shareholder Returns",
        "en": "Shareholder Returns · 股东回报分配",
    },
    "section.nav.ma_goodwill": {
        "zh": "併購與商譽審計 · M&A & Goodwill",
        "en": "M&A & Goodwill · 并购与商誉审计",
    },
    "section.nav.earnings_quality": {
        "zh": "盈利質量審計 · Earnings Quality",
        "en": "Earnings Quality · 盈利质量审计",
    },
    "section.nav.checklist": {
        "zh": "資本配置清單 · Principles Checklist",
        "en": "Principles Checklist · 资本配置清单",
    },
    "section.nav.ledger": {
        "zh": "原始審計底表 · Raw Ledger",
        "en": "Raw Ledger · 原始审计底表",
    },

    # ── sections: summary ────────────────────────────────────────────────
    "metric.label.company": {
        "zh": "標的名稱 / 代碼",
        "en": "Company / Ticker",
    },
    "metric.label.years": {
        "zh": "統計年限",
        "en": "Years Covered",
    },
    "metric.label.currency_unit": {
        "zh": "財報幣種 / 金額單位",
        "en": "Reporting Currency / Unit",
    },
    "metric.label.market_currency": {
        "zh": "市場幣種",
        "en": "Market Currency",
    },
    "metric.unit.absolute": {
        "zh": "元",
        "en": "Raw",
    },

    # ── sections: capital allocation ─────────────────────────────────────
    "section.capital.title": {
        "zh": "累計資本流向 (Cumulative Capital Allocation / Sources & Uses)",
        "en": "Cumulative Capital Allocation (Sources & Uses)",
    },
    "section.capital.time_mode.label": {
        "zh": "選擇時間範圍維度 (Select Time Scope)",
        "en": "Select Time Scope",
    },
    "section.capital.time_mode.cumulative": {
        "zh": "任意區間累計分析 (Custom Cumulative Period)",
        "en": "Custom Cumulative Period",
    },
    "section.capital.time_mode.single_year": {
        "zh": "單一年度專項審計 (Single Fiscal Year Audit)",
        "en": "Single Fiscal Year Audit",
    },
    "section.capital.year_range": {
        "zh": "選擇時間區間 (Select Year Range)",
        "en": "Select Year Range",
    },
    "section.capital.current_range": {
        "zh": "當前區間：**{start_year} - {end_year} ({n_years})**",
        "en": "Current Range: **{start_year} - {end_year} ({n_years})**",
    },
    "section.capital.single_year.label": {
        "zh": "選擇單年度 (Select Fiscal Year)",
        "en": "Select Fiscal Year",
    },
    "section.capital.current_single_year": {
        "zh": "當前單年度：**{year}**",
        "en": "Current Fiscal Year: **{year}**",
    },
    "section.capital.desc.single_year": {
        "zh": "追蹤 **{year}** 單一年度公司通過**經營活動賺取的現金流**，審計管理層如何在**資本支出、現金分紅、回購股份、投資併購**等渠道間分配資本。",
        "en": "Tracking the cash flow generated from **operations in FY {year}** and auditing how management allocates capital across **CapEx, dividends, buybacks, and M&A**.",
    },
    "section.capital.desc.cumulative": {
        "zh": "追蹤 **{start_year}-{end_year}** 年累計期間公司通過**經營活動賺取的累計現金流**，審計管理層如何在**資本支出、現金分紅、回購股份、投資併購**等渠道間分配資本。",
        "en": "Tracking the cumulative cash flow generated from **operations during {start_year}-{end_year}** and auditing how management allocates capital across **CapEx, dividends, buybacks, and M&A**.",
    },
    "section.capital.composition_rate": {
        "zh": "資本流向構成比率",
        "en": "Capital Allocation Composition Ratio",
    },
    "section.capital.diagnostics": {
        "zh": "資本分配率診斷",
        "en": "Capital Allocation Rate Diagnostics",
    },
    "section.capital.metric.capex_to_ocf": {
        "zh": "CapEx 佔 OCF 比例",
        "en": "CapEx / OCF",
    },
    "section.capital.metric.capex_to_ocf_help": {
        "zh": "企業重資產程度。該比例越低，說明企業創造自由現金流的能力越強。",
        "en": "Asset intensity of the business. A lower ratio indicates stronger free cash flow generation.",
    },
    "section.capital.metric.dividend_rate": {
        "zh": "現金分紅率",
        "en": "Dividend Payout Rate",
    },
    "section.capital.metric.dividend_rate_help": {
        "zh": "分配給股東的現金比例。",
        "en": "Proportion of operating cash flow distributed to shareholders as dividends.",
    },
    "section.capital.metric.buyback_rate": {
        "zh": "股份回購率",
        "en": "Share Buyback Rate",
    },
    "section.capital.metric.buyback_rate_help": {
        "zh": "利用多餘現金在公開市場回購股份註銷的力度。",
        "en": "Intensity of open-market share repurchases for cancellation. Higher is more aggressive return of capital.",
    },
    "section.capital.metric.ma_rate": {
        "zh": "併購與投資比率",
        "en": "M&A & Investment Rate",
    },
    "section.capital.metric.ma_rate_help": {
        "zh": "管理層通過投資或併購實現增長的力度。若該數值過高但 ROIIC 極低，可能是盲目擴張信號。",
        "en": "Management's intensity of pursuing growth through investment or M&A. If this ratio is high but ROIIC is low, it may signal wasteful empire-building.",
    },

    # ── sections: ROIC & ROIIC ───────────────────────────────────────────
    "section.roic.title": {
        "zh": "存量與增量資本配置回報率 (ROIC & ROIIC Capital Efficiency)",
        "en": "ROIC & ROIIC Capital Efficiency",
    },
    "section.roic.intro": {
        "zh": "巴菲特強調：投資人不僅要看當前的存量資本回報率 (ROIC)，更要看管理層“截留利潤進行再投資”時的增量回報率 (ROIIC)。",
        "en": "Buffett emphasizes that investors should look not only at the current return on invested capital (ROIC), but also at the incremental return on capital (ROIIC) when management reinvests retained earnings.",
    },
    "section.roic.intro.bullet1": {
        "zh": "1、**ROIC（存量回報率）**：衡量目前公司已投入資本的運營效率。",
        "en": "A. **ROIC (Return on Invested Capital)**: Measures the current operational efficiency of invested capital."
    },
    "section.roic.intro.bullet2": {
        "zh": "2、**ROIIC Retained（留存再投資回報率）**：ΔNOPAT / 累計留存盈餘。衡量管理層扣留盈利後，再投資的效率。",
        "en": "B. **ROIIC Retained (Incremental Return on Retained Earnings)**: ΔNOPAT / Cumulative Retained Earnings. Measures how efficiently management reinvests retained profits."
    },
    "section.roic.guidance.header": {
        "zh": "**指引**",
        "en": "**Guidance**",
    },
    "section.roic.guidance.bullet1": {
        "zh": "1、若 **ROIC 長期維持在 15% 以上**，表明公司產品或服務具備較強護城河。",
        "en": "A. If **ROIC is consistently above 15%**, the company likely possesses a durable economic moat.",
    },
    "section.roic.guidance.bullet2": {
        "zh": "2、若 **ROIIC 大幅低於 ROIC**，表明高回報的新投資機會可能正在減少，管理層應更多考慮分紅與回購。",
        "en": "B. If **ROIIC is significantly below ROIC**, high-return reinvestment opportunities may be dwindling; management should consider increasing dividends or buybacks.",
    },

    # ── sections: buyback ────────────────────────────────────────────────
    "section.buyback.title": {
        "zh": "股份回購與紅利分配 (Share Repurchase & Dividend Efficacy)",
        "en": "Share Repurchase & Dividend Efficacy",
    },
    "section.buyback.intro": {
        "zh": "本模塊對比**實際回購成交均價**和**保守每股內在價值 (DCF)**，甄別管理層是在低估時回購創造複利，還是在高估時回購毀滅價值。",
        "en": "This module compares the **actual weighted average repurchase price** against the **conservative intrinsic value per share (DCF)** to determine whether management is buying back shares at a discount (creating compound value) or at a premium (destroying value).",
    },
    "section.buyback.detail_header": {
        "zh": "歷年回購決策審計明細",
        "en": "Yearly Buyback Decision Audit Details",
    },
    "section.buyback.col.total_dividends": {
        "zh": "現金派息總額 ({currency})",
        "en": "Total Cash Dividends ({currency})",
    },
    "section.buyback.col.buyback_paid": {
        "zh": "回購現金支出 ({currency})",
        "en": "Buyback Cash Paid ({currency})",
    },
    "section.buyback.col.buyback_shares": {
        "zh": "回購股份數量（股）",
        "en": "Shares Repurchased",
    },
    "section.buyback.col.buyback_price": {
        "zh": "實際回購均價 ({currency})",
        "en": "Actual Buyback Avg Price ({currency})",
    },
    "section.buyback.col.intrinsic_value": {
        "zh": "每股估算內在價值 ({currency})",
        "en": "Est. Intrinsic Value/Share ({currency})",
    },
    "section.buyback.col.buyback_to_intrinsic": {
        "zh": "回購均價 / 內在價值",
        "en": "Buyback Price / Intrinsic Value",
    },
    "section.buyback.col.audit_rating": {
        "zh": "回購效率審計結論",
        "en": "Buyback Audit Rating",
    },

    # ── buyback ratings ──────────────────────────────────────────────────
    "buyback.rating.none": {
        "zh": "無顯著回購",
        "en": "No Significant Buyback",
    },
    "buyback.rating.excellent": {
        "zh": "卓越回購（創造價值）",
        "en": "Excellent Buyback (Value-Creating)",
    },
    "buyback.rating.reasonable": {
        "zh": "合理回購（公允對價）",
        "en": "Reasonable Buyback (Fair Price)",
    },
    "buyback.rating.blind": {
        "zh": "盲目回購（摧毀價值）",
        "en": "Blind Buyback (Value-Destroying)",
    },

    # ── sections: M&A & Goodwill ─────────────────────────────────────────
    "section.ma.title": {
        "zh": "併購與商譽資本效率審計 (M&A & Goodwill Capital Efficiency)",
        "en": "M&A & Goodwill Capital Efficiency Audit",
    },
    "section.ma.intro": {
        "zh": "警惕“帝國建造者”：用高溢價併購堆砌規模，卻無法讓併購支出賺回資本成本。",
        "en": "Beware the \"Empire Builder\": piling up scale through high-premium M&A without earning the cost of capital on acquisition spending.",
    },
    "section.ma.intro.bullet1": {
        "zh": "1、**商譽 / 股東權益**：攀升意味着資產負債表愈發依賴併購溢價，減值風險積聚。",
        "en": "A. **Goodwill / Equity**: A rising ratio means the balance sheet is increasingly dependent on acquisition premiums. Impairment risk is accumulating."
    },
    "section.ma.intro.bullet2": {
        "zh": "2、**Acquisition ROIIC**：ΔNOPAT / 累計併購支出。衡量併購資本是否賺回資本成本，低於 WACC 即為價值毀滅。",
        "en": "B. **Acquisition ROIIC**: ΔNOPAT / Cumulative M&A Spend. Measures whether acquisition capital earns its cost of capital. Below WACC = value destruction."
    },
    "section.ma.intro.bullet3": {
        "zh": "3、**商譽增速 vs NOPAT 增速**：正值代表商譽膨脹快於利潤增厚，併購未轉化為真實盈利。",
        "en": "C. **Goodwill Growth vs NOPAT Growth**: A positive gap means goodwill is ballooning faster than profit growth — acquisitions are not translating into real earnings."
    },
    "section.ma.col.ma_spend": {
        "zh": "累計併購現金支出",
        "en": "Cumulative M&A Cash Spend",
    },
    "section.ma.col.ma_spend_help": {
        "zh": "審計期間管理層用於併購/投資的累計現金。",
        "en": "Cumulative cash deployed by management for M&A/investment during the audit period.",
    },
    "section.ma.col.goodwill_balance": {
        "zh": "期末商譽餘額",
        "en": "Ending Goodwill Balance",
    },
    "section.ma.col.goodwill_balance_help": {
        "zh": "資產負債表上的商譽餘額，佔權益比越高減值風險越大。",
        "en": "Goodwill balance on the balance sheet. The higher it is relative to equity, the greater the impairment risk.",
    },
    "section.ma.col.goodwill_to_equity": {
        "zh": "商譽 / 股東權益",
        "en": "Goodwill / Equity",
    },
    "section.ma.col.goodwill_to_equity_help": {
        "zh": "商譽佔股東權益比例。",
        "en": "Goodwill as a percentage of shareholders' equity.",
    },
    "section.ma.col.acquisition_roiic": {
        "zh": "Acquisition ROIIC（最新）",
        "en": "Acquisition ROIIC (Latest)",
    },
    "section.ma.col.acquisition_roiic_help": {
        "zh": "併購支出的增量資本回報率，低於 WACC 即價值毀滅。",
        "en": "Incremental return on acquisition spending. Below WACC means value destruction.",
    },
    "section.ma.warning.gw_growth": {
        "zh": "商譽增速顯著超過 NOPAT 增速（差值 +{diff:.1%}），併購溢價持續堆積但未能等比例轉化為經營利潤，警惕未來商譽減值。",
        "en": "Goodwill growth significantly exceeds NOPAT growth (gap +{diff:.1%}). Acquisition premiums are piling up without a commensurate increase in operating profit. Watch for future goodwill impairment.",
    },
    "section.ma.success.gw_growth": {
        "zh": "NOPAT 增速超過商譽增速（差值 {diff:.1%}），併購整合見效，利潤增厚快於商譽膨脹。",
        "en": "NOPAT growth exceeds goodwill growth (gap {diff:.1%}). Acquisition integration is bearing fruit — profit growth outpaces goodwill inflation.",
    },
    "section.ma.guidance.header": {
        "zh": "**指引**",
        "en": "**Guidance**",
    },
    "section.ma.guidance.bullet1": {
        "zh": "1、若 **商譽 / 股東權益 > 50%** 且 **Acquisition ROIIC < WACC**，管理層大概率在用高溢價併購毀滅價值。",
        "en": "A. If **Goodwill / Equity > 50%** and **Acquisition ROIIC < WACC**, management is likely destroying value through high-premium acquisitions.",
    },
    "section.ma.guidance.bullet2": {
        "zh": "2、若累計併購支出可觀但 NOPAT 增量微弱，應質疑併購戰略而非會計處理。",
        "en": "B. If cumulative M&A spend is substantial but NOPAT growth is negligible, question the M&A strategy rather than the accounting.",
    },

    # ── sections: earnings quality ───────────────────────────────────────
    "section.eq.title": {
        "zh": "盈利質量與應計項審計 (Earnings Quality & Accruals Audit)",
        "en": "Earnings Quality & Accruals Audit",
    },
    "section.eq.intro": {
        "zh": "巴菲特強調“所有者盈餘”而非會計利潤：真正屬於股東的是現金，不是應計項。",
        "en": "Buffett emphasizes \"Owner Earnings\" over accounting profit: what truly belongs to shareholders is cash, not accruals.",
    },
    "section.eq.intro.bullet1": {
        "zh": "1、**所有者盈餘 vs 淨利潤**：長期低於淨利潤，說明盈利被維持性資本支出或非現金項侵蝕。",
        "en": "A. **Owner Earnings vs Net Profit**: Persistently below net profit means earnings are being eroded by maintenance capex or non-cash items."
    },
    "section.eq.intro.bullet2": {
        "zh": "2、**FCF / 淨利潤**：現金轉化率，低於 80% 需警惕，低於 50% 說明盈利高度依賴應計項。",
        "en": "B. **FCF / Net Profit**: Cash conversion rate. Below 80% warrants caution; below 50% means earnings are heavily dependent on accruals."
    },
    "section.eq.intro.bullet3": {
        "zh": "3、**應計項比率**：$(淨利潤 - 經營現金流) / 投入資本$，持續走高是會計激進的紅旗信號（Sloan 異常）。",
        "en": "C. **Accruals Ratio**: $(Net Profit - Operating Cash Flow) / Invested Capital$. A persistently rising ratio is a red flag for accounting aggressiveness (the Sloan anomaly)."
    },
    "section.eq.intro.bullet4": {
        "zh": "4、**每股所有者盈餘 (OEPS)**：巴菲特真正在意的“每股內在增長”口徑。",
        "en": "D. **Owner Earnings Per Share (OEPS)**: The Buffett-preferred measure of intrinsic per-share growth."
    },
    "section.eq.metric.oe_to_np": {
        "zh": "所有者盈餘 / 淨利潤",
        "en": "OE / Net Profit",
    },
    "section.eq.metric.oe_to_np_help": {
        "zh": "低於 100% 說明所有者盈餘不及會計利潤，盈利被維持性資本支出或非現金項侵蝕。",
        "en": "Below 100% means owner earnings lag accounting profit; earnings are eroded by maintenance capex or non-cash items.",
    },
    "section.eq.metric.fcf_to_ni": {
        "zh": "FCF / 淨利潤",
        "en": "FCF / Net Profit",
    },
    "section.eq.metric.fcf_to_ni_help": {
        "zh": "現金轉化率，越高說明盈利含金量越足。",
        "en": "Cash conversion rate. Higher is better — more of the earnings are backed by cash.",
    },
    "section.eq.metric.accruals_ratio": {
        "zh": "應計項比率",
        "en": "Accruals Ratio",
    },
    "section.eq.metric.accruals_ratio_help": {
        "zh": "正值且走高意味着淨利潤超過經營現金流，會計利潤含應計項偏重。",
        "en": "A positive and rising ratio means net profit exceeds operating cash flow — accounting profit is accrual-heavy.",
    },
    "section.eq.metric.oeps": {
        "zh": "每股所有者盈餘 (OEPS)",
        "en": "Owner Earnings Per Share (OEPS)",
    },
    "section.eq.metric.oeps_help": {
        "zh": "巴菲特真正在意的每股內在增長口徑。",
        "en": "The per-share intrinsic growth measure that Buffett truly cares about.",
    },
    "section.eq.oeps_cagr": {
        "zh": "近 {n_years} 年所有者盈餘年複合增速 (OEPS CAGR)：**{cagr:.1%}**。",
        "en": "{n_years}-Year Owner Earnings CAGR: **{cagr:.1%}**.",
    },
    "section.eq.guidance.header": {
        "zh": "**指引**",
        "en": "**Guidance**",
    },
    "section.eq.guidance.bullet1": {
        "zh": "1、若 **所有者盈餘長期 < 淨利潤**，需覈查資本支出結構與非現金調整項，盈利質量可能被高估。",
        "en": "A. If **Owner Earnings persistently < Net Profit**, examine the capex structure and non-cash adjustments — earnings quality may be overstated.",
    },
    "section.eq.guidance.bullet2": {
        "zh": "2、若 **應計項比率持續為正且攀升**，結合應收賬款與存貨週轉排查收入確認激進風險。",
        "en": "B. If the **accruals ratio is persistently positive and rising**, investigate revenue recognition aggressiveness risks in conjunction with AR and inventory turnover.",
    },

    # ── sections: checklist ──────────────────────────────────────────────
    "section.checklist.title": {
        "zh": "資本配置原則清單 (Capital Allocation Principles Checklist)",
        "en": "Capital Allocation Principles Checklist",
    },
    "section.checklist.intro": {
        "zh": "以下八條原則基於巴菲特式的資本配置檢查清單，每條原則展示**客觀事實數據**與**基準對比**，由系統自動計算判定狀態。用戶應結合行業特性與公司生命週期階段，對未通過或警告的原則進行深入研究。",
        "en": "The following eight principles are based on a Buffett-style capital allocation checklist. Each principle presents **objective factual data** against a **benchmark**, with the status determined automatically by the system. Users should further investigate failed or warning principles in light of industry characteristics and the company's lifecycle stage.",
    },
    "section.checklist.principle_n": {
        "zh": "原則 {index}",
        "en": "Principle {index}",
    },
    "section.checklist.actual_value": {
        "zh": "實際值：",
        "en": "Actual Value: ",
    },
    "section.checklist.benchmark": {
        "zh": "基準：",
        "en": "Benchmark: ",
    },
    "section.checklist.summary_header": {
        "zh": "**彙總**：{summary}。",
        "en": "**Summary**: {summary}.",
    },
    "section.checklist.disclaimer1": {
        "zh": "本清單提供事實數據和客觀判定，不構成投資建議。",
        "en": "This checklist provides factual data and objective assessments and does not constitute investment advice.",
    },
    "section.checklist.disclaimer2": {
        "zh": "請結合行業基準、競爭格局和管理層歷史決策背景進行獨立判斷。",
        "en": "Please exercise independent judgment in light of industry benchmarks, competitive landscape, and management's historical decision-making context.",
    },

    # ── badge texts ──────────────────────────────────────────────────────
    "badge.pass": {
        "zh": "[ ✔ 通過 ]",
        "en": "[ ✔ PASS ]",
    },
    "badge.fail": {
        "zh": "[ ✘ 未通過 ]",
        "en": "[ ✘ FAIL ]",
    },
    "badge.warning": {
        "zh": "[ ! 警告 ]",
        "en": "[ ! WARNING ]",
    },
    "badge.insufficient_data": {
        "zh": "[ ? 數據不足 ]",
        "en": "[ ? INSUFFICIENT DATA ]",
    },

    # ── sections: ledger ─────────────────────────────────────────────────
    "section.ledger.title": {
        "zh": "審計模型數據底表 (Raw Data & Intermediaries)",
        "en": "Audit Model Raw Data & Intermediaries",
    },
    "section.ledger.intro": {
        "zh": "以下為系統輸入參數、核心中間指標以及最終審計指標：",
        "en": "Below are the system input parameters, core intermediate indicators, and final audit metrics:",
    },
    "section.ledger.export_csv": {
        "zh": "導出完整審計表格為 CSV (Export to CSV)",
        "en": "Export Full Audit Table as CSV",
    },
    "section.ledger.duckdb_title": {
        "zh": "本地 DuckDB 緩存數據庫實時診斷 (DuckDB SQL Diagnostics)",
        "en": "Local DuckDB Cache Database Live Diagnostics (DuckDB SQL Diagnostics)",
    },
    "section.ledger.duckdb_intro": {
        "zh": "本系統採用高能進程內 SQL 數據庫 **DuckDB** 存儲和管理從 API 抓取的數據。您可以在下方選擇常用的診斷 SQL，或者直接編寫自定義 SQL，實時檢索並審查本地 DuckDB 緩存內容：",
        "en": "This system uses the high-performance in-process SQL database **DuckDB** to store and manage data fetched from APIs. You can select commonly used diagnostic SQL queries below, or write custom SQL to retrieve and review the local DuckDB cache content in real time:",
    },
    "section.ledger.sql_template.label": {
        "zh": "選擇常用 SQL 模板",
        "en": "Select SQL Template",
    },
    "section.ledger.sql_template.latest_financials": {
        "zh": "查看最新 10 條財務底表數據",
        "en": "View Latest 10 Financial Records",
    },
    "section.ledger.sql_template.exchange_rates": {
        "zh": "查看緩存的匯率底表數據",
        "en": "View Cached Exchange Rate Data",
    },
    "section.ledger.sql_template.stock_prices": {
        "zh": "查看緩存的股價底表數據",
        "en": "View Cached Stock Price Data",
    },
    "section.ledger.sql_template.audit_inputs": {
        "zh": "查看所有成功緩存過的股票輸入記錄",
        "en": "View All Successfully Cached Stock Input Records",
    },
    "section.ledger.sql_template.custom": {
        "zh": "編寫自定義 SQL 語句",
        "en": "Write Custom SQL",
    },
    "section.ledger.sql.editor_label": {
        "zh": "SQL 編輯器",
        "en": "SQL Editor",
    },
    "section.ledger.sql.placeholder": {
        "zh": "例如: SELECT * FROM raw_financials WHERE ticker = '0388.HK';",
        "en": "e.g.: SELECT * FROM raw_financials WHERE ticker = '0388.HK';",
    },
    "section.ledger.sql.success": {
        "zh": "SQL 執行成功",
        "en": "SQL Executed Successfully",
    },
    "section.ledger.sql.error": {
        "zh": "SQL 執行失敗: {exc}",
        "en": "SQL Execution Failed: {exc}",
    },
    "section.ledger.sql.no_cache": {
        "zh": "緩存數據庫 `audit.db` 尚未建立。請從左側通過 Futu 接口拉取並分析任意港股實時數據以進行初始化。",
        "en": "The cache database `audit.db` has not been created yet. Please fetch and analyze any HK stock data via the Futu interface from the sidebar to initialize.",
    },
    "section.ledger.sql.init_error": {
        "zh": "無法初始化 DuckDB 診斷工具: {exc}",
        "en": "Unable to Initialize DuckDB Diagnostic Tool: {exc}",
    },

    # ── charts: waterfall ────────────────────────────────────────────────
    "chart.waterfall.label.ocf": {
        "zh": "經營現金流（總流入）",
        "en": "Operating Cash Flow (Inflow)",
    },
    "chart.waterfall.label.capex": {
        "zh": "資本支出 (CapEx)",
        "en": "Capital Expenditure (CapEx)",
    },
    "chart.waterfall.label.dividends": {
        "zh": "現金分紅",
        "en": "Cash Dividends",
    },
    "chart.waterfall.label.buybacks": {
        "zh": "股份回購",
        "en": "Share Buybacks",
    },
    "chart.waterfall.label.ma": {
        "zh": "投資與併購",
        "en": "Investment & M&A",
    },
    "chart.waterfall.label.other": {
        "zh": "其他現金 / 債務留存",
        "en": "Other Cash / Debt Retention",
    },
    "chart.waterfall.hover": {
        "zh": "{label}<br>金額: {sign}{amount:.1f}{suffix}",
        "en": "{label}<br>Amount: {sign}{amount:.1f}{suffix}",
    },
    "chart.waterfall.title.cumulative": {
        "zh": "{start_year} - {end_year} 年累計資本分配去向瀑布圖（單位：{unit_label}）",
        "en": "{start_year} - {end_year} Cumulative Capital Allocation Waterfall (Unit: {unit_label})",
    },
    "chart.waterfall.title.single": {
        "zh": "{year} 年度單年資本分配去向瀑布圖（單位：{unit_label}）",
        "en": "{year} Single-Year Capital Allocation Waterfall (Unit: {unit_label})",
    },
    "chart.pie.label.capex": {
        "zh": "資本支出 (CapEx)",
        "en": "Capital Expenditure (CapEx)",
    },
    "chart.pie.label.dividends": {
        "zh": "現金分紅",
        "en": "Cash Dividends",
    },
    "chart.pie.label.buybacks": {
        "zh": "股份回購",
        "en": "Share Buybacks",
    },
    "chart.pie.label.ma": {
        "zh": "投資併購",
        "en": "Investment & M&A",
    },
    "chart.pie.label.other": {
        "zh": "其他現金 / 債務留存",
        "en": "Other Cash / Debt Retention",
    },

    # ── charts: ROIC ─────────────────────────────────────────────────────
    "chart.roic.trace.roic": {
        "zh": "ROIC（存量回報率）",
        "en": "ROIC (Stock Return)",
    },
    "chart.roic.trace.roiic_retained": {
        "zh": "ROIIC Retained（{window} 年滾動增量，滯後 {lag} 年）",
        "en": "ROIIC Retained ({window}-Year Rolling, {lag}-Year Lag)",
    },
    "chart.roic.title": {
        "zh": "ROIC 與 ROIIC（留存盈餘視角）趨勢",
        "en": "ROIC vs. ROIIC (Retained Earnings Perspective) Trend",
    },
    "chart.roic.xaxis": {
        "zh": "年份",
        "en": "Year",
    },
    "chart.roic.yaxis": {
        "zh": "回報率",
        "en": "Return",
    },

    # ── charts: buyback ──────────────────────────────────────────────────
    "chart.buyback.trace.intrinsic": {
        "zh": "保守每股內在價值（折算為市場幣種）",
        "en": "Conservative Intrinsic Value/Share (Market Currency)",
    },
    "chart.buyback.trace.avg_price": {
        "zh": "年平均交易股價",
        "en": "Annual Average Trading Price",
    },
    "chart.buyback.trace.buyback_price": {
        "zh": "實際股份回購均價",
        "en": "Actual Buyback Avg Price",
    },
    "chart.buyback.title": {
        "zh": "每股內在價值（估值錨）vs. 年度均價 vs. 實際回購成交價",
        "en": "Intrinsic Value/Share (Valuation Anchor) vs. Avg Price vs. Actual Buyback Price",
    },
    "chart.buyback.yaxis": {
        "zh": "價格 ({currency})",
        "en": "Price ({currency})",
    },

    # ── charts: M&A / Goodwill ───────────────────────────────────────────
    "chart.ma.trace.goodwill_to_equity": {
        "zh": "商譽 / 股東權益",
        "en": "Goodwill / Equity",
    },
    "chart.ma.trace.ma_spend": {
        "zh": "併購現金支出 ({suffix})",
        "en": "M&A Cash Spend ({suffix})",
    },
    "chart.ma.trace.acquisition_roiic": {
        "zh": "Acquisition ROIIC（{window} 年滾動，滯後 {lag} 年）",
        "en": "Acquisition ROIIC ({window}-Year Rolling, {lag}-Year Lag)",
    },
    "chart.ma.title": {
        "zh": "商譽佔比、併購支出與併購資本回報率",
        "en": "Goodwill Ratio, M&A Spend & Acquisition ROIIC",
    },
    "chart.ma.yaxis": {
        "zh": "回報率 / 佔比",
        "en": "Return / Ratio",
    },
    "chart.ma.yaxis2": {
        "zh": "併購支出",
        "en": "M&A Spend",
    },

    # ── charts: earnings quality ─────────────────────────────────────────
    "chart.eq.trace.net_profit": {
        "zh": "淨利潤",
        "en": "Net Profit",
    },
    "chart.eq.trace.owner_earnings": {
        "zh": "所有者盈餘",
        "en": "Owner Earnings",
    },
    "chart.eq.trace.fcf": {
        "zh": "自由現金流",
        "en": "Free Cash Flow",
    },
    "chart.eq.trace.accruals_ratio": {
        "zh": "應計項比率",
        "en": "Accruals Ratio",
    },
    "chart.eq.title": {
        "zh": "淨利潤 vs 所有者盈餘 vs 自由現金流（含應計項比率）",
        "en": "Net Profit vs Owner Earnings vs FCF (with Accruals Ratio)",
    },
    "chart.eq.yaxis": {
        "zh": "金額 ({suffix})",
        "en": "Amount ({suffix})",
    },
    "chart.eq.yaxis2": {
        "zh": "應計項比率",
        "en": "Accruals Ratio",
    },

    # ── chart generic ────────────────────────────────────────────────────
    "chart.xaxis.year": {
        "zh": "年份",
        "en": "Year",
    },
    "chart.unit.billions": {
        "zh": "十億",
        "en": "Billions",
    },
    "chart.unit.millions": {
        "zh": "百萬",
        "en": "Millions",
    },

    # =====================================================================
    #  CHECKLIST PRINCIPLE TITLES
    # =====================================================================
    "checklist.p1.title": {
        "zh": "資本回報率是否高於資本成本？",
        "en": "Is ROIC above the cost of capital?",
    },
    "checklist.p2.title": {
        "zh": "留存利潤是否被高效再投資？",
        "en": "Is retained profit reinvested efficiently?",
    },
    "checklist.p3.title": {
        "zh": "每 $1 留存是否創造 >$1 市值？",
        "en": "Does every $1 retained create >$1 market value?",
    },
    "checklist.p4.title": {
        "zh": "回購是否具有紀律性（低於內在價值）？",
        "en": "Are buybacks disciplined (below intrinsic value)?",
    },
    "checklist.p5.title": {
        "zh": "分紅是否被自由現金流覆蓋？",
        "en": "Are dividends covered by free cash flow?",
    },
    "checklist.p6.title": {
        "zh": "資本效率趨勢是否改善？",
        "en": "Is the capital efficiency trend improving?",
    },
    "checklist.p7.title": {
        "zh": "併購是否創造高於資本成本的價值？",
        "en": "Do acquisitions create value above the cost of capital?",
    },
    "checklist.p8.title": {
        "zh": "盈利質量是否健康（現金轉化）？",
        "en": "Is earnings quality healthy (cash-backed)?",
    },

    # =====================================================================
    #  CHECKLIST P1: ROIC vs WACC
    # =====================================================================
    "checklist.p1.value.negative_ic": {
        "zh": "極高 (Negative IC)",
        "en": "Extremely High (Negative IC)",
    },
    "checklist.p1.benchmark.wacc_spread": {
        "zh": "WACC {wacc:.1%}（利差 {spread:+.1%}）",
        "en": "WACC {wacc:.1%} (Spread {spread:+.1%})",
    },
    "checklist.p1.desc.insufficient": {
        "zh": "ROIC 數據不足，無法判斷是否創造價值。",
        "en": "Insufficient ROIC data to determine whether value is being created.",
    },
    "checklist.p1.desc.money_printer": {
        "zh": "公司近 5 年平均投入資本為負或零，且稅後經營利潤 (NOPAT) 持續為正。這意味着公司不需要股東與債權人投入額外本金，便能靠經營性負債與豐沛現金流運轉（零/負投入資本擴張），屬於商業壁壘極高的特許經營“印鈔機”型公司，其資本效率極高，回報率視為無限大！",
        "en": "The company's 5-year average invested capital is negative or zero, while NOPAT remains consistently positive. This means the company does not require additional capital from shareholders or creditors — it can operate on operational liabilities and abundant cash flow (zero/negative invested capital expansion). This is a franchise \"money printer\" with extremely high business barriers, and its capital efficiency is treated as infinite!",
    },
    "checklist.p1.desc.pass": {
        "zh": "近 5 年平均 ROIC {avg_roic:.1%} 高於 WACC {wacc:.1%}，利差 +{spread:.1%}，公司持續創造經濟價值。",
        "en": "5-year average ROIC of {avg_roic:.1%} exceeds WACC of {wacc:.1%}, with a spread of +{spread:.1%}. The company is consistently creating economic value.",
    },
    "checklist.p1.desc.fail": {
        "zh": "近 5 年平均 ROIC {avg_roic:.1%} 低於 WACC {wacc:.1%}，利差 {spread:.1%}，公司在毀滅股東價值。",
        "en": "5-year average ROIC of {avg_roic:.1%} is below WACC of {wacc:.1%}, with a spread of {spread:.1%}. The company is destroying shareholder value.",
    },

    # =====================================================================
    #  CHECKLIST P2: ROIIC vs ROIC
    # =====================================================================
    "checklist.p2.benchmark.negative_ic": {
        "zh": "ROIC 極高 (Negative IC)",
        "en": "ROIC Extremely High (Negative IC)",
    },
    "checklist.p2.value.capital_light": {
        "zh": "極高 (Capital-Light)",
        "en": "Extremely High (Capital-Light)",
    },
    "checklist.p2.desc.insufficient": {
        "zh": "ROIIC 數據不足，無法評估增量再投資效率。",
        "en": "Insufficient ROIIC data to assess incremental reinvestment efficiency.",
    },
    "checklist.p2.desc.capital_light": {
        "zh": "公司在過去 {window} 年累計未留下任何盈餘（可能全部用於分紅與回購），但稅後經營利潤 (NOPAT) 仍然實現了增長。這代表了極其優異的“零資本 / 輕資產擴張模式”，邊際增量再投資效率極高！",
        "en": "The company retained no earnings over the past {window} years (likely fully distributed as dividends and buybacks), yet NOPAT still grew. This represents an exceptional \"zero-capital / asset-light expansion\" model with extremely high marginal reinvestment efficiency!",
    },
    "checklist.p2.desc.inf_roic_pass": {
        "zh": "雖然因存量投入資本為負使得存量 ROIC 視為無限大，但公司增量再投資回報率 (ROIIC) 達到 {roiic:.1%}，遠高於 WACC {wacc:.1%}，管理層的增量資金部署依然極其高效。",
        "en": "Although stock ROIC is treated as infinite due to negative invested capital, the company's incremental ROIIC reaches {roiic:.1%}, far above the WACC of {wacc:.1%}. Management's incremental capital deployment remains highly efficient.",
    },
    "checklist.p2.desc.inf_roic_fail": {
        "zh": "雖然存量 ROIC 視為無限大，但公司增量再投資回報率 (ROIIC) 僅為 {roiic:.1%}，低於資本成本 WACC {wacc:.1%}，說明留存利潤的邊際使用效率低下，應加大分紅或回購。",
        "en": "Although stock ROIC is treated as infinite, the company's incremental ROIIC is only {roiic:.1%}, below the cost of capital (WACC {wacc:.1%}). The marginal efficiency of retained earnings is poor — the company should increase dividends or buybacks.",
    },
    "checklist.p2.desc.ge_avg": {
        "zh": "ROIIC {roiic:.1%} ≥ ROIC {roic:.1%}，增量投資回報不低於存量資本，管理層仍能找到高回報投資機會。",
        "en": "ROIIC of {roiic:.1%} ≥ ROIC of {roic:.1%}. Incremental returns are at least as good as existing capital returns — management is still finding high-return investment opportunities.",
    },
    "checklist.p2.desc.ge_wacc": {
        "zh": "ROIIC {roiic:.1%} < ROIC {roic:.1%}，邊際效率遞減，但仍高於 WACC {wacc:.1%}，再投資仍在創造價值但護城河可能收窄。",
        "en": "ROIIC of {roiic:.1%} < ROIC of {roic:.1%}. Marginal efficiency is declining, but still above WACC of {wacc:.1%}. Reinvestment is still creating value, though the moat may be narrowing.",
    },
    "checklist.p2.desc.lt_wacc": {
        "zh": "ROIIC {roiic:.1%} < WACC {wacc:.1%}，增量投資回報低於資本成本，管理層在低效擴張，應轉向分紅或回購。",
        "en": "ROIIC of {roiic:.1%} < WACC of {wacc:.1%}. Incremental returns are below the cost of capital. Management is expanding inefficiently and should pivot to dividends or buybacks.",
    },

    # =====================================================================
    #  CHECKLIST P3: One-Dollar Rule
    # =====================================================================
    "checklist.p3.desc.insufficient": {
        "zh": "一美元原則數據不足，無法評估市值創造效率。",
        "en": "Insufficient one-dollar-rule data to assess market value creation efficiency.",
    },
    "checklist.p3.desc.pass": {
        "zh": "每留存 $1 創造了 ${value:.2f} 市值，市場對管理層的資本配置投出信任票。",
        "en": "Every $1 retained created ${value:.2f} in market value. The market votes confidence in management's capital allocation.",
    },
    "checklist.p3.desc.warning": {
        "zh": "每留存 $1 僅創造 ${value:.2f} 市值，留存利潤的市場認可度不足，資本配置效率存疑。",
        "en": "Every $1 retained created only ${value:.2f} in market value. Market recognition of retained earnings is inadequate — capital allocation efficiency is questionable.",
    },
    "checklist.p3.desc.fail": {
        "zh": "每留存 $1 僅創造 ${value:.2f} 市值，管理層截留利潤卻未能轉化為市場價值，嚴重摧毀股東財富。",
        "en": "Every $1 retained created only ${value:.2f} in market value. Management is hoarding profits without converting them into market value — severely destroying shareholder wealth.",
    },

    # =====================================================================
    #  CHECKLIST P4: Buyback Discipline
    # =====================================================================
    "checklist.p4.benchmark.le_085": {
        "zh": "≤ 0.85x 內在價值",
        "en": "≤ 0.85x Intrinsic Value",
    },
    "checklist.p4.value.ratio": {
        "zh": "{ratio:.2f}x 內在價值",
        "en": "{ratio:.2f}x Intrinsic Value",
    },
    "checklist.p4.desc.insufficient": {
        "zh": "審計期間無顯著回購記錄，無法評估回購紀律。",
        "en": "No significant buyback activity during the audit period. Unable to assess buyback discipline.",
    },
    "checklist.p4.desc.pass": {
        "zh": "加權回購均價為內在價值的 {ratio:.2f}x，管理層在低估時回購，實實在在地增厚長期股東權益。",
        "en": "Weighted average buyback price is {ratio:.2f}x intrinsic value. Management is buying back shares at a discount, genuinely enhancing long-term shareholder equity.",
    },
    "checklist.p4.desc.warning": {
        "zh": "加權回購均價為內在價值的 {ratio:.2f}x，回購價格接近公允價值，未造成重大價值損失但也未創造顯著超額回報。",
        "en": "Weighted average buyback price is {ratio:.2f}x intrinsic value. The buyback price is near fair value — no significant value destruction, but no meaningful excess returns either.",
    },
    "checklist.p4.desc.fail": {
        "zh": "加權回購均價為內在價值的 {ratio:.2f}x，管理層在高估時回購，用真金白銀補貼離場股東，損害長期持有者利益。",
        "en": "Weighted average buyback price is {ratio:.2f}x intrinsic value. Management is buying back at a premium, using real cash to subsidize exiting shareholders at the expense of long-term holders.",
    },

    # =====================================================================
    #  CHECKLIST P5: FCF Coverage
    # =====================================================================
    "checklist.p5.benchmark": {
        "zh": "FCF 派發率 ≤ 100%",
        "en": "FCF Payout Ratio ≤ 100%",
    },
    "checklist.p5.value.neg_fcf": {
        "zh": "N/A（FCF 為負）",
        "en": "N/A (Negative FCF)",
    },
    "checklist.p5.desc.insufficient": {
        "zh": "審計期間未進行現金分紅或回購，無法評估分紅可持續性。",
        "en": "No cash dividends or buybacks during the audit period. Unable to assess dividend sustainability.",
    },
    "checklist.p5.desc.neg_fcf": {
        "zh": "累計自由現金流為負，公司在舉債分紅或回購，不可持續。",
        "en": "Cumulative free cash flow is negative. The company is borrowing to fund dividends or buybacks — this is unsustainable.",
    },
    "checklist.p5.desc.pass": {
        "zh": "FCF 派發率 {ratio:.1%}，分紅與回購完全被自由現金流覆蓋，可持續。",
        "en": "FCF payout ratio of {ratio:.1%}. Dividends and buybacks are fully covered by free cash flow — sustainable.",
    },
    "checklist.p5.desc.warning": {
        "zh": "FCF 派發率 {ratio:.1%}，分紅略超自由現金流，長期可能需舉債維持，需關注。",
        "en": "FCF payout ratio of {ratio:.1%}. Distributions slightly exceed free cash flow — may require borrowing to sustain in the long term. Monitor closely.",
    },
    "checklist.p5.desc.fail": {
        "zh": "FCF 派發率 {ratio:.1%}，分紅大幅超出自由現金流，不可持續，存在毀滅價值風險。",
        "en": "FCF payout ratio of {ratio:.1%}. Distributions significantly exceed free cash flow — unsustainable and poses a value-destruction risk.",
    },

    # =====================================================================
    #  CHECKLIST P6: ROIC Trend
    # =====================================================================
    "checklist.p6.benchmark.trend": {
        "zh": "ROIC 趨勢",
        "en": "ROIC Trend",
    },
    "checklist.p6.value.sustained_inf": {
        "zh": "持續極高 (Negative IC)",
        "en": "Sustained Extremely High (Negative IC)",
    },
    "checklist.p6.benchmark.excellent": {
        "zh": "持續優秀",
        "en": "Sustained Excellence",
    },
    "checklist.p6.value.leap": {
        "zh": "{first_roic:.1%} → 極高",
        "en": "{first_roic:.1%} → Extremely High",
    },
    "checklist.p6.benchmark.improving": {
        "zh": "持續改善",
        "en": "Continuously Improving",
    },
    "checklist.p6.value.slip": {
        "zh": "極高 → {last_roic:.1%}",
        "en": "Extremely High → {last_roic:.1%}",
    },
    "checklist.p6.benchmark.advantage": {
        "zh": "保持優勢",
        "en": "Maintaining Advantage",
    },
    "checklist.p6.benchmark.trend_val": {
        "zh": "趨勢 {trend:+.1%}",
        "en": "Trend {trend:+.1%}",
    },
    "checklist.p6.desc.insufficient": {
        "zh": "ROIC 數據不足，無法判斷趨勢方向。",
        "en": "Insufficient ROIC data to determine the trend direction.",
    },
    "checklist.p6.desc.insufficient_points": {
        "zh": "ROIC 數據點不足（需至少 2 年），無法判斷趨勢。",
        "en": "Insufficient ROIC data points (at least 2 years required) to determine the trend.",
    },
    "checklist.p6.desc.sustained_inf": {
        "zh": "公司近 {n_years} 年起始與期末的存量 ROIC 均視為無限大（持續處於負投入資本運轉的“印鈔機”狀態），經營壁壘和資信佔資優勢極其穩固，資本效率卓越且穩定。",
        "en": "The company's ROIC has been treated as infinite throughout the past {n_years} years (continuously operating in a \"money printer\" state with negative invested capital). Its business moat and credit-based funding advantage are extremely solid — capital efficiency is outstanding and stable.",
    },
    "checklist.p6.desc.leap": {
        "zh": "公司近 {n_years} 年 ROIC 從起始年份的 {first_roic:.1%} 跨越式躍升至期末年份的無限大（成功轉型為零/負投入資本運轉的印鈔機狀態），商業模式和資信壁壘呈現爆發式改善。",
        "en": "ROIC leapt from {first_roic:.1%} at the start to infinity at the end over the past {n_years} years (successfully transforming into a zero/negative invested capital money printer). The business model and credit barrier have improved explosively.",
    },
    "checklist.p6.desc.slip": {
        "zh": "公司近 {n_years} 年 ROIC 從起始年份的無限大（負投入資本印鈔機狀態）跌落至期末年份的 {last_roic:.1%}，說明公司的負投入資本紅利有所收窄，或商業渠道優勢發生鬆動，護城河出現侵蝕跡象。",
        "en": "ROIC has fallen from infinity (negative invested capital money printer) at the start to {last_roic:.1%} at the end over the past {n_years} years. The company's negative-invested-capital advantage is shrinking, or its commercial channel advantage is weakening — signs of moat erosion.",
    },
    "checklist.p6.desc.improve": {
        "zh": "近 {n_years} 年 ROIC 從 {first_roic:.1%} 提升至 {last_roic:.1%}（+{trend:.1%}），護城河持續加固。",
        "en": "ROIC improved from {first_roic:.1%} to {last_roic:.1%} over the past {n_years} years (+{trend:.1%}). The moat continues to strengthen.",
    },
    "checklist.p6.desc.stable": {
        "zh": "近 {n_years} 年 ROIC 從 {first_roic:.1%} 變動至 {last_roic:.1%}（{trend:+.1%}），基本穩定但需關注。",
        "en": "ROIC moved from {first_roic:.1%} to {last_roic:.1%} over the past {n_years} years ({trend:+.1%}). Generally stable but warrants attention.",
    },
    "checklist.p6.desc.decline": {
        "zh": "近 {n_years} 年 ROIC 從 {first_roic:.1%} 下滑至 {last_roic:.1%}（{trend:.1%}），護城河明顯侵蝕。",
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
        "zh": "ROIC 極高 / WACC {wacc:.1%}",
        "en": "ROIC Extremely High / WACC {wacc:.1%}",
    },
    "checklist.p7.value.excellent": {
        "zh": "極高",
        "en": "Extremely High",
    },
    "checklist.p7.desc.insufficient": {
        "zh": "審計期間無顯著併購支出，或 Acquisition ROIIC 數據不足，無法評估併購資本效率。",
        "en": "No significant M&A spending during the audit period, or insufficient Acquisition ROIIC data to assess M&A capital efficiency.",
    },
    "checklist.p7.desc.excellent": {
        "zh": "Acquisition ROIIC 極為卓越（無限大），併購支出高效地創造了無需本金投入的額外稅後經營利潤！",
        "en": "Acquisition ROIIC is exceptionally high (infinite). M&A spending has efficiently created additional NOPAT without requiring additional invested capital!",
    },
    "checklist.p7.desc.inf_roic_pass": {
        "zh": "雖然因存量投入資本為負使得存量 ROIC 視為無限大，但公司併購增量回報率 (Acquisition ROIIC) 達到 {roiic:.1%}，高於 WACC {wacc:.1%}，管理層的外延併購資金配置極其成功。",
        "en": "Although stock ROIC is treated as infinite due to negative invested capital, Acquisition ROIIC reaches {roiic:.1%}, above WACC of {wacc:.1%}. Management's M&A capital deployment has been extremely successful.",
    },
    "checklist.p7.desc.inf_roic_fail": {
        "zh": "雖然存量 ROIC 視為無限大，但公司併購增量回報率 (Acquisition ROIIC) 僅為 {roiic:.1%}，低於 WACC {wacc:.1%}，表明外延併購在低效消耗資金，未能跑贏基本資金成本。",
        "en": "Although stock ROIC is treated as infinite, Acquisition ROIIC is only {roiic:.1%}, below WACC of {wacc:.1%}. This indicates M&A is inefficiently consuming capital and failing to beat the basic cost of capital.",
    },
    "checklist.p7.desc.ge_avg": {
        "zh": "Acquisition ROIIC {roiic:.1%} ≥ ROIC {roic:.1%}，併購支出帶來的增量回報不低於存量資本，管理層在為股東創造價值。",
        "en": "Acquisition ROIIC of {roiic:.1%} ≥ ROIC of {roic:.1%}. Incremental returns from M&A are at least as good as existing capital returns — management is creating shareholder value.",
    },
    "checklist.p7.desc.ge_wacc": {
        "zh": "Acquisition ROIIC {roiic:.1%} < ROIC {roic:.1%}，併購回報邊際遞減但仍高於 WACC {wacc:.1%}，併購尚在創造價值但溢價紀律需警惕。",
        "en": "Acquisition ROIIC of {roiic:.1%} < ROIC of {roic:.1%}. M&A returns are marginally declining but still above WACC of {wacc:.1%}. M&A is still creating value, but premium discipline needs monitoring.",
    },
    "checklist.p7.desc.lt_wacc": {
        "zh": "Acquisition ROIIC {roiic:.1%} < WACC {wacc:.1%}，併購支出回報低於資本成本，管理層疑似正在毀滅股東價值。",
        "en": "Acquisition ROIIC of {roiic:.1%} < WACC of {wacc:.1%}. M&A returns are below the cost of capital. Management appears to be destroying shareholder value.",
    },

    # =====================================================================
    #  CHECKLIST P8: Earnings Quality
    # =====================================================================
    "checklist.p8.benchmark": {
        "zh": "FCF / 淨利潤 ≥ 80%",
        "en": "FCF / Net Profit ≥ 80%",
    },
    "checklist.p8.desc.insufficient": {
        "zh": "審計期間無正淨利潤年度，無法評估盈利的現金支撐度。",
        "en": "No positive net profit years during the audit period. Unable to assess cash backing of earnings.",
    },
    "checklist.p8.desc.pass": {
        "zh": "近 {n_years} 年平均 FCF/淨利潤 {ratio:.1%}，盈利高度由自由現金流支撐，會計利潤含金量充足。",
        "en": "{n_years}-year average FCF/Net Profit of {ratio:.1%}. Earnings are strongly backed by free cash flow — accounting profit quality is solid.",
    },
    "checklist.p8.desc.warning": {
        "zh": "近 {n_years} 年平均 FCF/淨利潤 {ratio:.1%}，現金轉化偏低，應計項偏重，盈利質量需結合應收與存貨進一步覈查。",
        "en": "{n_years}-year average FCF/Net Profit of {ratio:.1%}. Cash conversion is on the low side with a bias towards accruals — earnings quality warrants further investigation against AR and inventory.",
    },
    "checklist.p8.desc.fail": {
        "zh": "近 {n_years} 年平均 FCF/淨利潤 {ratio:.1%}，自由現金流遠低於會計利潤，盈利高度依賴應計項，質量存疑。",
        "en": "{n_years}-year average FCF/Net Profit of {ratio:.1%}. Free cash flow is far below accounting profit — earnings are heavily dependent on accruals and quality is questionable.",
    },

    # ── checklist summary (callable) ─────────────────────────────────────
    "checklist.summary": {
        "zh": lambda pass_count, total, warning_count, fail_count, insufficient_count:
            f"{pass_count}/{total} 原則通過"
            + (f"，{warning_count} 條警告" if warning_count > 0 else "")
            + (f"，{fail_count} 條未通過" if fail_count > 0 else "")
            + (f"，{insufficient_count} 條數據不足" if insufficient_count > 0 else ""),
        "en": lambda pass_count, total, warning_count, fail_count, insufficient_count:
            f"{pass_count}/{total} principles passed"
            + (f", {warning_count} warning(s)" if warning_count > 0 else "")
            + (f", {fail_count} failed" if fail_count > 0 else "")
            + (f", {insufficient_count} insufficient data" if insufficient_count > 0 else ""),
    },

    # ── error messages ──────────────────────────────────────────────────
    "error.wacc_le_terminal": {
        "zh": "折現率 WACC 必須大於永續增長率。",
        "en": "WACC must be greater than the terminal growth rate.",
    },
}
