# 资本配置效率审计系统

这是一个基于 Streamlit 的交互式财务审计仪表盘，用于评估上市公司管理层在资本配置上的效率与纪律。系统从结构化财务数据出发，计算 ROIC、ROIIC、所有者盈余、一美元原则、DCF 内在价值、股份回购有效性等指标，并生成“巴菲特式”资本配置原则清单。

项目支持从 Futu OpenD 实时拉取港股历史财报并自动保存至本地 DuckDB 缓存进行分析，也支持上传自定义 JSON 财报数据。

## 主要功能

- 资本分配流向分析：展示经营现金流在资本支出、分红、回购、并购和留存现金之间的分配情况。
- ROIC 与 ROIIC 分析：评估存量投入资本回报率，以及管理层留存利润再投资后的增量回报效率。
- 股份回购审计：对比实际回购均价与 DCF 估算的每股内在价值，判断回购是否创造股东价值。
- 并购与商誉审计：激活商誉占比、并购支出强度与 Acquisition ROIIC，识别"帝国建造者"用高溢价并购毁灭价值的行为。
- 盈利质量审计：对比净利润、所有者盈余与自由现金流，追踪应计项比率与每股所有者盈余 (OEPS)，识破会计利润粉饰。
- 巴菲特原则清单：基于 8 条客观原则（ROIC vs WACC、ROIIC vs ROIC、一美元原则、回购纪律、FCF 覆盖、趋势检查、并购资本效率、盈利质量）自动生成事实判定，辅助价值投资研究。
- 标准化底表导出：展示并导出模型计算后的审计底表，便于复核和二次分析。
- 审计报告导出：支持生成 PDF（固定排版，适合打印存档）和 HTML（交互式图表，零系统依赖，适合屏幕浏览与分享）两种格式的完整审计报告。
- 自定义参数：支持调整维持性资本支出比例、WACC、阶段增长率和永续增长率。

## 技术栈

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Pydantic
- WeasyPrint（PDF 报告生成，可选）
- Kaleido（PDF 图表静态化，可选）

## 项目结构

```text
.
├── app.py                  # 审计主应用 Streamlit 入口
├── hkex_app.py             # HKEX 股本变动工作台 Streamlit 入口（独立子应用）
├── hkex_app/               # 子应用包（i18n/主题/存储/图表/页面，与主应用解耦）
├── core/
│   ├── auditor.py          # 审计模块轻量编排器
│   ├── buyback_audit.py    # 股份回购纪律审计
│   ├── calculator.py       # 财务指标计算与数据加工
│   ├── checklist.py        # 巴菲特资本配置原则清单
│   └── valuation.py        # 两阶段 DCF 内在价值估算
├── datalayer/              # 数据访问层（行情接口适配/缓存/归一化管理）
│   ├── cache.py            # DuckDB 本地缓存读写
│   ├── manager.py          # 数据管理器（缓存命中 → API 拉取 → 持久化）
│   ├── normalizer.py       # 财务数据清洗与归一化
│   └── providers/          # 行情 API 适配器（Futu / HKEX 月报表等）
├── models/
│   └── input_schema.py     # 输入数据结构与校验规则
├── services/
│   ├── audit_pipeline.py   # 自动化审计流水线
│   ├── charts.py           # Plotly 图表构造工具（供 UI 与报告共享）
│   └── report/             # PDF/HTML 报告生成模块
│       ├── builder.py      # 报告编排器（组装数据 → HTML → PDF）
│       ├── renderer.py     # Plotly 图表 → PNG 静态化
│       ├── sections.py     # 七大审计板块 HTML 片段构建
│       └── template.py     # Jinja2 HTML 模板与 CSS 样式
├── scripts/
│   └── hkex_sync.py        # HKEX 月报表抓取同步 CLI（大区间回填推荐）
├── tests/                  # 核心量化逻辑与子应用存储单元测试
├── ui/                     # 审计主应用 Streamlit 页面与侧边栏模块
├── requirements.txt        # Python 依赖
└── README.md
```

## 快速开始

1. 创建并激活虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

> **PDF 报告功能额外系统依赖**：WeasyPrint 需要 cairo/pango/gdk-pixbuf 系统库。
>
> - macOS：`brew install cairo pango gdk-pixbuf libffi`
> - Ubuntu/Debian：`sudo apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev`
> - 仅使用 PDF 导出功能时需要；Streamlit 仪表盘本身无需这些系统库。

3. 启动应用：

```bash
streamlit run app.py
```

4. 在浏览器中打开 Streamlit 提供的本地地址，通常为：

```text
http://localhost:8501
```

## HKEX 股本变动工作台（独立应用）

`hkex_app.py` 是与审计主应用 `app.py` 完全解耦的独立 Streamlit 工具，专用于港交所「证券变动月报表」的抓取、浏览与对比。所有子应用模块位于 `hkex_app/` 包内，不共享 `ui/`、`services/`、`core/` 与根 `i18n/`，仅复用底层 `datalayer/` 抓取与缓存层（`DatabaseCache` 作父类扩展、`HkexShareCapitalFetcher` 直接调用）。

```bash
streamlit run hkex_app.py
```

功能：

- **查看数据**：选 ticker 与年份范围，展示股本变动趋势折线图（已发行不含库存 / 库存股 / 总发行三条线）与明细表格，附最新一期、较最早变化率等摘要指标。
- **抓取数据**：交互式替代 `scripts/hkex_sync.py`，支持显式日期区间与增量模式（从最新记录次日）、force 重抓、限速与重试配置；抓取后进入审阅面板，勾选确认后方写入 DuckDB。
- **多 Ticker 对比**：2–5 只股票总发行股本曲线横向对比，支持绝对值与归一化（首期=100）两种量纲。
- **记录管理**：逐条删除或单期强制重抓已入库记录；底部「危险区」可清空整只 ticker 的全部记录（折叠 + 二次确认）。

子应用自带独立 i18n（中英双语，默认 English，语言状态与主应用互不干扰）与独立视觉风格。多 Ticker、多年份的大区间全量回填仍建议使用 `scripts/hkex_sync.py` CLI，避免 UI 长时间阻塞。

> 子应用测试：`python -m unittest tests.test_hkex_app_store`

## 审计报告导出

在侧边栏「审计报告导出」分区选择报告格式（HTML 或 PDF），点击「生成审计报告」按钮，系统会基于当前载入的财务数据和参数生成一份完整的审计报告，包含：

- **封面**：公司元信息、统计年限、币种、生成时间。
- **执行摘要**：8 条巴菲特原则的通过/警告/未通过/数据不足计数汇总。
- **七大审计板块**：累计资本流向、ROIC & ROIIC、股份回购、并购与商誉、盈利质量、原则清单、审计底表，与 Streamlit 仪表盘各维度一一对应。
- **参数附录**：记录生成报告时的全部 AuditParams（WACC、增长率、维持性资本支出比例、ROIIC 窗口与滞后年数等），便于复核。
- **免责声明**：复用仪表盘的免责声明。

### 两种格式对比

| 特性 | HTML · 交互式 | PDF · 固定排版 |
|---|---|---|
| 图表 | 可交互 Plotly（hover/缩放/图例切换） | 静态高清 PNG |
| 系统依赖 | 无（仅需 Python 包） | cairo/pango/gdk-pixbuf 系统库 |
| 生成速度 | ~1 秒 | ~30 秒（含 Chromium 渲染） |
| 文件体积 | ~4.7 MB（内联 Plotly.js，离线可用） | ~540 KB |
| 适用场景 | 屏幕浏览、邮件分享、内网托管 | 打印存档、正式提交 |
| 离线可用 | 是（Plotly.js 内联） | 是 |

报告使用与仪表盘一致的 Courier Prime "old-money" 排版风格，中英双语自动随当前界面语言切换。HTML 报告为零依赖路径，推荐优先使用；PDF 报告需额外安装系统库（见下方说明）。

## 数据输入

系统支持三种数据来源：

- 通过富途牛牛 (Futu OpenD) 实时拉取港股历史财务数据（默认推荐）。
- 上传符合结构要求的 JSON 财报文件。

应用侧边栏提供了 JSON 输入模板下载功能，可直接下载模板后填入公司财务数据。

### JSON 数据结构示例

```json
{
  "ticker": "0388.HK",
  "company_name": "香港交易所",
  "currency": "RMB",
  "amount_unit": "million",
  "market_currency": "HKD",
  "exchange_rate_to_reporting_currency": [0.89, 0.83, 0.86, 0.91, 0.91],
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
```

所有 `financials` 字段数组长度以及 `exchange_rate_to_reporting_currency` 长度必须与 `years` 长度一致，否则会触发 Pydantic 数据校验错误。

## 核心指标说明

| 指标 | 含义 |
| --- | --- |
| NOPAT | 税后经营利润，按 `EBIT * (1 - tax_rate)` 计算。 |
| Invested Capital | 投入资本，按 `股东权益 + 有息债务 - 现金及等价物` 计算。 |
| ROIC | 存量投入资本回报率，用于衡量当前业务资本效率。 |
| Owner Earnings | 所有者盈余，按 `净利润 + 折旧摊销 - 维持性资本支出` 估算。 |
| ROIIC | 增量投入资本回报率，用于衡量新增资本带来的利润增量。 |
| ROIIC Retained | 基于累计留存盈余的再投资回报率。 |
| One-Dollar Rule | 一美元原则，衡量每留存 1 元利润是否创造超过 1 元市值。 |
| Goodwill to Equity / IC | 商誉占股东权益 / 投入资本比例，攀升意味着减值风险积聚。 |
| MA to OCF | 并购现金支出占经营现金流比例，衡量并购资本强度。 |
| Acquisition ROIIC | 并购增量回报率，`ΔNOPAT / 累计并购支出`，低于 WACC 即价值毁灭。 |
| Goodwill vs NOPAT Growth | 商誉增速与 NOPAT 增速之差，正值代表并购未转化为真实盈利。 |
| FCF | 自由现金流，按 `经营现金流 - 资本支出` 计算。 |
| OE to Net Profit | 所有者盈余 / 净利润，长期低于 1 说明盈利被维持性资本支出侵蚀。 |
| FCF to Net Income | 自由现金流 / 净利润，衡量盈利的现金支撑度（现金转化率）。 |
| Accruals Ratio | 应计项比率 `(净利润 - 经营现金流) / 投入资本`，走高是会计激进信号。 |
| OEPS | 每股所有者盈余，巴菲特真正在意的"每股内在增长"口径。 |
| Intrinsic Value Share | 基于两阶段 DCF 模型估算的每股内在价值。 |
| Buyback Audit Rating | 基于回购均价与内在价值对比生成的回购效率评价。 |

## 巴菲特资本配置原则清单

系统基于巴菲特与芒格的资本配置检查清单，对管理层进行 8 条客观原则验证：

| 原则 | 检查内容 | 判定状态 |
| --- | --- | --- |
| 1. 资本回报率 > 资本成本 | ROIC vs WACC 利差 | ✅ pass / ❌ fail / ❓ insufficient_data |
| 2. 留存利润高效再投资 | ROIIC vs ROIC 对比 | ✅ pass / ⚠️ warning / ❌ fail |
| 3. 每 $1 留存创造 >$1 市值 | One-Dollar Rule 比率 | ✅ pass / ⚠️ warning / ❌ fail |
| 4. 回购纪律性 | 回购均价 vs DCF 内在价值 | ✅ pass / ⚠️ warning / ❌ fail |
| 5. 分红被 FCF 覆盖 | FCF 派发率 | ✅ pass / ⚠️ warning / ❌ fail |
| 6. 资本效率趋势 | ROIC 5 年起止对比 | ✅ pass / ⚠️ warning / ❌ fail |
| 7. 并购创造价值 | Acquisition ROIIC vs WACC/ROIC | ✅ pass / ⚠️ warning / ❌ fail / ❓ insufficient_data |
| 8. 盈利质量健康 | FCF / 净利润（近 5 年平均） | ✅ pass / ⚠️ warning / ❌ fail / ❓ insufficient_data |

系统展示每条原则的**实际值、基准和事实描述**，由用户结合行业特性与公司生命周期进行独立判断，不输出主观综合分数或投资建议。

## 测试

```bash
python -m unittest discover -s tests
```

## 使用建议

- 财务金额字段应保持同一币种、同一数量级口径；当前 `amount_unit` 固定为 `million`。
- `currency` 是财报本位币，所有财务金额字段都应按该币种录入。
- `market_currency` 是 `avg_stock_price` 的币种；系统会使用 `exchange_rate_to_reporting_currency` 将股价折算到 `currency` 后再计算市值和一美元原则。
- `shares_outstanding_m` 和 `buybacks_shares_m` 使用百万股口径。
- `buybacks_paid` 应使用财报本位币和 `amount_unit` 口径，确保回购均价能与每股内在价值同币种比较。
- 对于自定义公司数据，建议至少提供 5 年以上数据，以便 ROIIC 和一美元原则指标具备参考意义。
- DCF 参数会显著影响内在价值估算，应结合行业、利率和公司成长阶段审慎调整。

## 注意事项

本项目用于财务分析、管理层资本配置效率评估和投资研究辅助，不构成投资建议。模型结果依赖输入数据质量、会计口径和估值假设，实际决策前应结合原始财报、行业信息和独立判断进行复核。
