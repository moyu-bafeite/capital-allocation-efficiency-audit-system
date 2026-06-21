# 管理层资本配置效率审计系统

这是一个基于 Streamlit 的交互式财务审计仪表盘，用于评估上市公司管理层在资本配置上的效率与纪律。系统从结构化财务数据出发，计算 ROIC、ROIIC、所有者盈余、一美元原则、DCF 内在价值、股份回购有效性等指标，并生成综合量化评分与中文审计解读。

项目支持从富途牛牛（Futu OpenD）与雅虎财经（Yahoo Finance）实时拉取港股历史财报并自动保存至本地 DuckDB 缓存进行分析，也支持上传自定义 JSON 财报数据。

## 主要功能

- 资本分配流向分析：展示经营现金流在资本支出、分红、回购、并购和留存现金之间的分配情况。
- ROIC 与 ROIIC 分析：评估存量投入资本回报率，以及管理层留存利润再投资后的增量回报效率。
- 股份回购审计：对比实际回购均价与 DCF 估算的每股内在价值，判断回购是否创造股东价值。
- 综合评分卡：按 ROIC、ROIIC、一美元原则、回购纪律和分红适配度进行加权评分。
- 标准化底表导出：展示并导出模型计算后的审计底表，便于复核和二次分析。
- 自定义参数：支持调整维持性资本支出比例、WACC、阶段增长率和永续增长率。

## 技术栈

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Pydantic

## 项目结构

```text
.
├── app.py                  # Streamlit 应用入口
├── core/
│   ├── auditor.py          # 审计模块轻量编排器
│   ├── buyback_audit.py    # 股份回购纪律审计
│   ├── calculator.py       # 财务指标计算与数据加工
│   ├── commentary.py       # 中文审计解读生成
│   ├── scorecard.py        # 五维量化评分卡
│   └── valuation.py        # 两阶段 DCF 内在价值估算
├── data/                   # 本地缓存与数据存储目录
├── models/
│   └── input_schema.py     # 输入数据结构与校验规则
├── services/
│   └── audit_pipeline.py   # 自动化审计流水线
├── tests/                  # 核心量化逻辑单元测试
├── ui/                     # Streamlit 页面、侧边栏和图表模块
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

3. 启动应用：

```bash
streamlit run app.py
```

4. 在浏览器中打开 Streamlit 提供的本地地址，通常为：

```text
http://localhost:8501
```

## 数据输入

系统支持三种数据来源：

- 通过富途牛牛 (Futu OpenD) 实时拉取港股历史财务数据（默认推荐）。
- 通过雅虎财经 (Yahoo Finance) 实时拉取港股历史财务数据。
- 上传符合结构要求的 JSON 财报文件。

应用侧边栏提供了 JSON 输入模板下载功能，可直接下载模板后填入公司财务数据。

### JSON 数据结构示例

```json
{
  "ticker": "0700.HK",
  "company_name": "腾讯控股",
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
| Intrinsic Value Share | 基于两阶段 DCF 模型估算的每股内在价值。 |
| Buyback Audit Rating | 基于回购均价与内在价值对比生成的回购效率评价。 |

## 综合评分权重

| 维度 | 权重 |
| --- | ---: |
| ROIC 存量资产创利能力 | 30% |
| ROIIC 增量再投资能力 | 25% |
| 一美元原则市值创造效率 | 20% |
| 股份回购纪律 | 10% |
| 分红及再投资适配度 | 15% |

系统会根据加权得分生成 `A+`、`A`、`B`、`C`、`D`、`F` 等级，并输出中文分析意见。

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
