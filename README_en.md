# Capital Allocation Efficiency Audit System

An interactive Streamlit-based financial audit dashboard for evaluating the efficiency and discipline of listed company management's capital allocation. The system starts from structured financial data, calculates metrics such as ROIC, ROIIC, Owner Earnings, the One-Dollar Rule, DCF intrinsic value, and share buyback effectiveness, and generates a "Buffett-style" capital allocation principles checklist.

The project supports real-time fetching of Hong Kong stock historical financial reports from Futu OpenD with automatic caching to a local DuckDB database for analysis, and also supports uploading custom JSON financial data files.

## Key Features

- **Capital Allocation Flow Analysis**: Displays the distribution of operating cash flow across CapEx, dividends, buybacks, M&A, and retained cash.
- **ROIC & ROIIC Analysis**: Assesses return on existing invested capital and the incremental efficiency of reinvesting retained earnings.
- **Share Buyback Audit**: Compares actual weighted average buyback prices against DCF-estimated intrinsic value per share to determine whether buybacks create shareholder value.
- **M&A & Goodwill Audit**: Highlights goodwill-to-equity ratios, M&A spend intensity, and Acquisition ROIIC to identify "empire builders" destroying value through high-premium acquisitions.
- **Earnings Quality Audit**: Compares net profit, owner earnings, and free cash flow; tracks the accruals ratio and OEPS (Owner Earnings Per Share) to detect accounting profit embellishment.
- **Buffett Principles Checklist**: Automatically generates factual assessments based on 8 objective principles (ROIC vs WACC, ROIIC vs ROIC, One-Dollar Rule, buyback discipline, FCF coverage, trend check, M&A capital efficiency, earnings quality) to support value-investment research.
- **Standardized Ledger Export**: Displays and exports the model's computed audit ledger for review and secondary analysis.
- **Customizable Parameters**: Adjustable maintenance CapEx ratio, WACC, stage growth rates, and terminal growth rate.

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Pydantic

## Project Structure

```text
.
├── app.py                  # Streamlit application entry point
├── core/
│   ├── auditor.py          # Audit module lightweight orchestrator
│   ├── buyback_audit.py    # Share buyback discipline audit
│   ├── calculator.py       # Financial metric calculation & data processing
│   ├── checklist.py        # Buffett capital allocation principles checklist
│   └── valuation.py        # Two-stage DCF intrinsic value estimation
├── datalayer/              # Data access layer (market API adapters / cache / normalization)
│   ├── cache.py            # DuckDB local cache read/write
│   ├── manager.py          # Data manager (cache hit → API fetch → persist)
│   ├── normalizer.py       # Financial data cleaning & normalization
│   └── providers/          # Market API adapters (Futu, etc.)
├── i18n/                   # Internationalization module
│   ├── i18n.py             # Translation engine (t() function, Translatable)
│   └── translations.py     # Translation catalog (zh + en)
├── models/
│   └── input_schema.py     # Input data structure & validation rules
├── services/
│   ├── audit_pipeline.py   # Automated audit pipeline
│   ├── charts.py           # Plotly chart builders (shared by UI and reports)
│   └── report/             # PDF/HTML report generator
│       ├── builder.py      # Report orchestrator (data → HTML → PDF)
│       ├── renderer.py     # Plotly charts → static PNG
│       ├── sections.py     # Seven audit section HTML fragment builders
│       └── template.py     # Jinja2 HTML template & CSS styles
├── tests/                  # Core quantitative logic unit tests
├── ui/                     # Streamlit pages & sidebar modules
├── requirements.txt        # Python dependencies
└── README.md
```

## Quick Start

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the application:

```bash
streamlit run app.py
```

4. Open the local URL provided by Streamlit in your browser, typically:

```text
http://localhost:8501
```

### Language Switching

The UI supports both Chinese (default) and English. Use the language selector at the top of the sidebar to switch between languages.

## Data Input

The system supports three data sources:

- Real-time fetching of HK stock historical financial data via Futu OpenD (default, recommended).
- Uploading a structured JSON financial data file.

The app sidebar provides a JSON input template download feature — download the template directly and fill in the company's financial data.

### JSON Data Structure Example

```json
{
  "ticker": "0388.HK",
  "company_name": "Hong Kong Exchanges",
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

All `financials` field array lengths and the `exchange_rate_to_reporting_currency` length must match the `years` length, or Pydantic validation errors will be triggered.

## Core Indicator Descriptions

| Indicator | Meaning |
| --- | --- |
| NOPAT | Net Operating Profit After Tax, computed as `EBIT * (1 - tax_rate)`. |
| Invested Capital | `Shareholders' Equity + Interest-Bearing Debt - Cash & Equivalents`. |
| ROIC | Return on existing invested capital, measuring current business capital efficiency. |
| Owner Earnings | Estimated as `Net Profit + D&A - Maintenance CapEx`. |
| ROIIC | Incremental return on invested capital, measuring the profit increment from new capital deployed. |
| ROIIC Retained | Reinvestment return based on cumulative retained earnings. |
| One-Dollar Rule | Measures whether every $1 of retained profit creates more than $1 of market capitalization. |
| Goodwill to Equity / IC | Goodwill as a percentage of equity / invested capital. A rising ratio signals growing impairment risk. |
| MA to OCF | M&A cash spend as a proportion of operating cash flow, measuring M&A capital intensity. |
| Acquisition ROIIC | `ΔNOPAT / Cumulative M&A Spend`. Below WACC means value destruction. |
| Goodwill vs NOPAT Growth | The gap between goodwill growth rate and NOPAT growth rate. A positive gap means acquisitions have not translated into real earnings. |
| FCF | Free Cash Flow, computed as `Operating Cash Flow - CapEx`. |
| OE to Net Profit | Owner Earnings / Net Profit. Persistently below 1 means earnings are being eroded by maintenance CapEx. |
| FCF to Net Income | FCF / Net Profit, measuring the cash backing of earnings (cash conversion rate). |
| Accruals Ratio | `(Net Profit - Operating Cash Flow) / Invested Capital`. A rising ratio is a red flag for accounting aggressiveness. |
| OEPS | Owner Earnings Per Share — Buffett's preferred measure of per-share intrinsic growth. |
| Intrinsic Value Share | Estimated intrinsic value per share based on a two-stage DCF model. |
| Buyback Audit Rating | A buyback efficiency rating generated by comparing the actual buyback average price against intrinsic value. |

## Buffett Capital Allocation Principles Checklist

The system validates management against 8 objective principles based on the Buffett-Munger capital allocation checklist:

| # | Principle | Check | Status |
|---|---|---|---|
| 1 | ROIC > Cost of Capital | ROIC vs WACC spread | ✅ pass / ❌ fail / ❓ insufficient_data |
| 2 | Retained earnings reinvested efficiently | ROIIC vs ROIC comparison | ✅ pass / ⚠️ warning / ❌ fail |
| 3 | Every $1 retained creates >$1 market value | One-Dollar Rule ratio | ✅ pass / ⚠️ warning / ❌ fail |
| 4 | Buybacks are disciplined | Buyback price vs DCF intrinsic value | ✅ pass / ⚠️ warning / ❌ fail |
| 5 | Dividends covered by FCF | FCF payout ratio | ✅ pass / ⚠️ warning / ❌ fail |
| 6 | Capital efficiency trend improving | ROIC start vs end (5 years) | ✅ pass / ⚠️ warning / ❌ fail |
| 7 | Acquisitions create value | Acquisition ROIIC vs WACC/ROIC | ✅ pass / ⚠️ warning / ❌ fail / ❓ insufficient_data |
| 8 | Earnings quality healthy | FCF / Net Profit (5-year avg.) | ✅ pass / ⚠️ warning / ❌ fail / ❓ insufficient_data |

The system displays the **actual value, benchmark, and factual description** for each principle. Users should exercise independent judgment in light of industry characteristics and the company's lifecycle stage. No subjective composite score or investment advice is provided.

## Testing

```bash
python -m unittest discover -s tests
```

## Usage Recommendations

- Financial amount fields should maintain the same currency and denomination; `amount_unit` currently defaults to `million`.
- `currency` is the reporting currency; all financial amount fields should be entered in this currency.
- `market_currency` is the currency of `avg_stock_price`; the system uses `exchange_rate_to_reporting_currency` to convert stock prices to `currency` before computing market cap and the One-Dollar Rule.
- `shares_outstanding_m` and `buybacks_shares_m` use millions-of-shares denomination.
- `buybacks_paid` should use the reporting currency and `amount_unit` denomination to ensure the buyback average price can be compared with intrinsic value per share in the same currency.
- For custom company data, at least 5 years of data is recommended for ROIIC and One-Dollar Rule indicators to be meaningful.
- DCF parameters significantly affect intrinsic value estimates and should be adjusted carefully based on industry, interest rates, and the company's growth stage.

## Important Notes

This project is for financial analysis, management capital allocation efficiency evaluation, and investment research support purposes only and does not constitute investment advice. Model results depend on input data quality, accounting conventions, and valuation assumptions. Actual decisions should be cross-checked against original financial reports, industry information, and independent judgment.
