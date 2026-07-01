import unittest
import numpy as np

from core.calculator import FinancialCalculator
from models.input_schema import CompanyAuditInput


def make_sample_input() -> CompanyAuditInput:
    return CompanyAuditInput(
        ticker="TEST",
        company_name="Test Company",
        currency="USD",
        amount_unit="million",
        market_currency="USD",
        exchange_rate_to_reporting_currency=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        closing_exchange_rate_to_reporting_currency=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        years=[2020, 2021, 2022, 2023, 2024, 2025],
        financials={
            "net_profit": [100, 120, 140, 160, 180, 200],
            "ebit": [120, 150, 180, 210, 240, 270],
            "tax_rate": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
            "interest_expense": [5, 5, 5, 5, 5, 5],
            "total_equity": [500, 550, 600, 650, 700, 750],
            "short_term_debt": [50, 50, 50, 50, 50, 50],
            "long_term_debt": [100, 100, 100, 100, 100, 100],
            "cash_and_equivalents": [50, 50, 50, 50, 50, 50],
            "operating_cash_flow": [130, 150, 170, 190, 210, 230],
            "capex": [40, 40, 40, 40, 40, 40],
            "da": [20, 20, 20, 20, 20, 20],
            "dividends_paid": [20, 20, 20, 20, 20, 20],
            "buybacks_paid": [0, 0, 10, 0, 20, 0],
            "buybacks_shares": [0, 0, 1000000, 0, 2000000, 0],
            "ma_paid": [5, 5, 5, 5, 5, 5],
            "goodwill": [10, 10, 10, 10, 10, 10],
            "shares_outstanding": [100000000, 99000000, 98000000, 97000000, 96000000, 95000000],
            "avg_stock_price": [10, 11, 12, 13, 14, 15],
            "closing_stock_price": [10.5, 10.0, 13.0, 12.5, 15.0, 14.0],
        },
    )


class FinancialCalculatorTest(unittest.TestCase):
    def test_base_metrics_are_calculated(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df

        self.assertEqual(df.loc[2020, "NOPAT"], 96)
        self.assertEqual(df.loc[2020, "Invested_Capital"], 600)
        # Owner Earnings now derives from OpIncBeforeWC (default 0 when not
        # provided) minus maintenance capex, tax-adjusted:
        # (0 - 20 - 0) * (1 - 0.2) = -16
        self.assertEqual(df.loc[2020, "Owner_Earnings"], -16)
        # Period-end market cap = shares × closing_price × closing_FX.
        # 100M shares × 10.5 close × 1.0 FX = 1.05B; in millions → 1050.
        self.assertEqual(df.loc[2020, "Market_Cap"], 1050)

    def test_market_cap_uses_period_end_basis(self):
        """Market_Cap must use closing_stock_price (not avg) × closing FX."""
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df
        for i, year in enumerate([2020, 2021, 2022, 2023, 2024, 2025]):
            shares = 100000000 - i * 1000000  # 100M, 99M, 98M, ...
            close = [10.5, 10.0, 13.0, 12.5, 15.0, 14.0][i]
            expected_mc = shares * close * 1.0 / 1e6  # million unit, FX=1
            self.assertAlmostEqual(
                df.loc[year, "Market_Cap"], expected_mc, places=6,
                msg=f"Market_Cap for {year} should use closing price {close}, not avg",
            )
        # Sanity: avg-based market cap would differ for at least one year.
        self.assertNotEqual(
            df.loc[2020, "Market_Cap"],
            100000000 * 10 / 1e6,  # avg-based would be 1000
        )

    def test_processed_df_contains_roiic_and_one_dollar_rule(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        self.assertIn("ROIIC_Retained_3Y", df.columns)
        self.assertIn("ROIIC_Retained_5Y", df.columns)
        self.assertIn("One_Dollar_Rule_5Y", df.columns)
        self.assertAlmostEqual(df.loc[2023, "ROIIC_Retained_3Y"], 72 / 290)

    def test_invalid_maintenance_capex_ratio_is_rejected(self):
        with self.assertRaises(ValueError):
            FinancialCalculator(make_sample_input(), maintenance_capex_ratio=1.5)

    def test_owner_earnings_uses_opinc_before_wc_with_tax(self):
        """Owner Earnings = (OpIncBeforeWC - maint_capex - maintenance_ΔWC) × (1-tax).
        OpIncBeforeWC already embeds non-cash add-backs (D&A, impairment, fair
        value), so we feed it directly rather than reconstructing from pieces.
        """
        sample_input = make_sample_input()
        # Provide OpIncBeforeWC so OE is driven by it.
        # 2020: OpIncBeforeWC=150, maint_capex=20, ΔWC=0 (no revenue/WC fields)
        # -> pre_tax_OE = 150 - 20 - 0 = 130 -> OE = 130 * 0.8 = 104
        # 2021: OpIncBeforeWC=170, maint_capex=20, ΔWC=0
        # -> pre_tax_OE = 170 - 20 - 0 = 150 -> OE = 150 * 0.8 = 120
        sample_input.financials.operating_income_before_wc_change = [150.0, 170.0, 0.0, 0.0, 0.0, 0.0]
        sample_input.financials.cash_from_business_operations = [150.0, 170.0, 0.0, 0.0, 0.0, 0.0]

        calculator = FinancialCalculator(sample_input, maintenance_capex_ratio=0.5)
        df = calculator.df

        self.assertEqual(df.loc[2020, "Owner_Earnings"], 104.0)
        self.assertEqual(df.loc[2021, "Owner_Earnings"], 120.0)

    def test_goodwill_and_ma_ratios(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: goodwill=10, total_equity=500, Invested_Capital=600 (from existing test), OCF=130, ma_paid=5
        self.assertAlmostEqual(df.loc[2020, "Goodwill_to_Equity"], 10 / 500)
        self.assertAlmostEqual(df.loc[2020, "Goodwill_to_IC"], 10 / 600)
        self.assertAlmostEqual(df.loc[2020, "MA_to_OCF"], 5 / 130)

    def test_earnings_quality_metrics(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: OCF=130, capex=40 -> FCF=90; net_profit=100 -> FCF/NI=0.9
        self.assertEqual(df.loc[2020, "FCF"], 90)
        self.assertAlmostEqual(df.loc[2020, "FCF_to_NetIncome"], 90 / 100)
        # Owner_Earnings 2020 = (OpIncBeforeWC(0) - maint_capex(20) - 0) * 0.8 = -16
        # OE/NI = -16 / 100
        self.assertAlmostEqual(df.loc[2020, "OE_to_NetProfit"], -16 / 100)
        # Accruals = (net_profit - OCF) / IC = (100 - 130) / 600 = -30/600
        self.assertAlmostEqual(df.loc[2020, "Accruals_Ratio"], (100 - 130) / 600)
        # OEPS = Owner_Earnings / shares_in_millions = -16 / 100
        self.assertAlmostEqual(df.loc[2020, "OEPS"], -16 / 100)

    def test_acquisition_roiic_in_processed_df(self):
        calculator = FinancialCalculator(make_sample_input(), maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        self.assertIn("Acquisition_ROIIC_3Y", df.columns)
        self.assertIn("Acquisition_ROIIC_5Y", df.columns)
        self.assertIn("Goodwill_vs_NOPAT_Growth_5Y", df.columns)

        # Acquisition ROIIC mirrors ROIIC_Retained structure: with lag=1 and ma_paid=5 each year,
        # at 2023 (window=3): NOPAT diff = NOPAT(2023)-NOPAT(2020); cumulative ma (lag 1) = 5*3 = 15
        # NOPAT 2020 = 120*0.8=96, NOPAT 2023 = 210*0.8=168 -> diff=72; 72/15 = 4.8
        self.assertAlmostEqual(df.loc[2023, "Acquisition_ROIIC_3Y"], 72 / 15)

    def test_acquisition_roiic_zero_ma_returns_nan(self):
        sample = make_sample_input()
        sample.financials.ma_paid = [0.0] * 6
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        # With zero M&A spend, cumulative_ma denominator is never positive -> all NaN
        self.assertTrue(df["Acquisition_ROIIC_3Y"].dropna().empty)

    def test_optimized_invested_capital_and_average_roic(self):
        sample = make_sample_input()
        sample.financials.short_term_deposits = [100.0, 50.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.time_deposits_non_current = [50.0, 30.0, 0.0, 0.0, 0.0, 0.0]
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df

        # 2020: total_equity(500) + debt(150) - cash_and_equiv(50) - short_term_deposits(100) - time_deposits_non_current(50) = 450
        self.assertEqual(df.loc[2020, "Invested_Capital"], 450.0)

        # 2021: total_equity(550) + debt(150) - cash_and_equiv(50) - short_term_deposits(50) - time_deposits_non_current(30) = 570
        self.assertEqual(df.loc[2021, "Invested_Capital"], 570.0)

        # 2021 average IC: (450 + 570) / 2 = 510
        # 2021 NOPAT: EBIT(150) * (1 - 0.2) = 120
        # 2021 ROIC: 120 / 510 = 0.235294...
        self.assertAlmostEqual(df.loc[2021, "ROIC"], 120.0 / 510.0)

    def test_capital_light_expansion_returns_inf(self):
        sample = make_sample_input()
        sample.financials.dividends_paid = [100, 120, 140, 160, 180, 200]
        sample.financials.buybacks_paid = [0, 0, 0, 0, 0, 0]

        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.get_processed_df(roiic_window_1=3, roiic_window_2=5, roiic_retained_lag=1)

        # In 2023, window=3, lag=1: cumulative retained for 2020+2021+2022 is 0.
        # NOPAT grows from 96 (2020) to 168 (2023), so nopat_diff = 72 > 0.
        # Expected value is np.inf
        self.assertEqual(df.loc[2023, "ROIIC_Retained_3Y"], np.inf)

    def test_lease_and_other_debt_added_to_invested_capital(self):
        """Lease liabilities, convertible bonds and notes payable must be
        added to the debt side of Invested Capital (IFRS 16 + other
        interest-bearing debt), increasing IC and lowering ROIC vs the
        traditional debt-only base."""
        sample = make_sample_input()
        # Base IC (2020) = equity(500) + debt(150) - cash(50) = 600
        # Add lease 60 + convertible 40 + notes 20 = +120 -> IC = 720
        sample.financials.lease_liability_current = [20.0] * 6
        sample.financials.lease_liability_non_current = [40.0] * 6
        sample.financials.convertible_bonds = [40.0] * 6
        sample.financials.notes_payable = [20.0] * 6
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df

        self.assertEqual(df.loc[2020, "total_lease_liability"], 60.0)
        self.assertEqual(df.loc[2020, "total_other_interest_bearing_debt"], 60.0)
        self.assertEqual(df.loc[2020, "Invested_Capital"], 720.0)

    def test_income_fair_value_and_impairment_excluded_from_nopat(self):
        """Income-statement fair value changes (gain) must be subtracted from
        EBIT and income-statement impairment (loss, abs-normalized) must be
        added back when computing NOPAT, so non-operating / non-cash items
        inside Operating Profit do not pollute operating profitability."""
        sample = make_sample_input()
        # 2020 baseline NOPAT = ebit(120) * (1 - 0.2) = 96
        # Add a 30 fair-value gain (subtracted) and 50 impairment loss (added back):
        # normalized OP = 120 - 30 + 50 = 140 -> NOPAT = 140 * 0.8 = 112
        sample.financials.income_fair_value_changes = [30.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.income_impairment_charges = [50.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df
        self.assertEqual(df.loc[2020, "NOPAT"], 112.0)

    def test_associates_and_joint_venture_added_to_nopat(self):
        """Share of profits of associates and joint ventures sits below
        operating profit and is already post-tax, so it is added directly to
        NOPAT (not grossed up by the tax rate)."""
        sample = make_sample_input()
        # Baseline NOPAT 2020 = 96. Add associates 24 + JV 16 = +40 -> 136
        sample.financials.share_of_profit_associates = [24.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.share_of_profit_joint_venture = [16.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df
        self.assertEqual(df.loc[2020, "NOPAT"], 136.0)

    def test_operating_interest_expense_added_back_to_nopat(self):
        """Issuers that deduct interest expense above Operating Profit (e.g.
        CK Asset 01113) must have it added back so Operating Profit is
        restored to a true EBIT before the tax shield is applied."""
        sample = make_sample_input()
        # Baseline NOPAT 2020 = 120 * 0.8 = 96.
        # Add operating_interest_expense 25 -> normalized OP = 120 + 25 = 145
        # -> NOPAT = 145 * 0.8 = 116
        sample.financials.operating_interest_expense = [25.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df
        self.assertEqual(df.loc[2020, "NOPAT"], 116.0)

    def test_derivative_assets_not_deducted_from_invested_capital(self):
        """Derivative financial assets are operating hedges, not excess cash.
        They must NOT be deducted from the liquid-cash pool when computing
        Invested Capital, otherwise IC is understated and ROIC overstated."""
        sample = make_sample_input()
        # Base IC 2020 = equity(500) + debt(150) - cash(50) = 600
        # Derivatives should NOT reduce IC.
        sample.financials.derivative_financial_assets_current = [30.0] * 6
        sample.financials.derivative_financial_assets_non_current = [70.0] * 6
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df
        # IC stays 600 — the 100 of derivatives is not subtracted.
        self.assertEqual(df.loc[2020, "Invested_Capital"], 600.0)

    def test_working_capital_ratio_reduces_owner_earnings(self):
        """maintenance_ΔWC = avg(WC_Ratio, 3Y) × ΔRevenue must be deducted
        from pre-tax Owner Earnings. A positive-WC company growing revenue
        consumes working capital, lowering OE."""
        sample = make_sample_input()
        # Set up a positive-WC company: WC = AR(40) + Inv(20) - AP(10) = 50
        # Revenue 2020=1000, 2021=1100 -> ΔRev = +100
        # WC_Ratio = 50/1000 = 0.05; avg (first year, min_periods=1) = 0.05
        # maintenance_ΔWC = 0.05 * 100 = 5
        # OpIncBeforeWC 2021 = 200, maint_capex = 20
        # pre_tax_OE = 200 - 20 - 5 = 175 -> OE = 175 * 0.8 = 140
        sample.financials.revenue = [1000.0, 1100.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.accounts_receivable = [40.0, 44.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.inventory = [20.0, 22.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.accounts_payable = [10.0, 11.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.operating_income_before_wc_change = [0.0, 200.0, 0.0, 0.0, 0.0, 0.0]
        sample.financials.cash_from_business_operations = [0.0, 195.0, 0.0, 0.0, 0.0, 0.0]
        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df
        # 2021: AR=44, Inv=22, AP=11 -> WC=55; WC_Ratio=55/1100=0.05
        # avg_wc_ratio (min_periods=1 at 2021 is 2-year avg since 2020 has data)
        # 2020 wc_ratio = 50/1000 = 0.05; 2021 = 0.05 -> avg = 0.05
        # delta_revenue 2021 = 1100-1000 = 100
        # maintenance_delta_wc = 0.05 * 100 = 5
        # OE = (200 - 20 - 5) * 0.8 = 140
        self.assertAlmostEqual(df.loc[2021, "wc_ratio"], 0.05)
        self.assertAlmostEqual(df.loc[2021, "maintenance_delta_wc"], 5.0)
        self.assertAlmostEqual(df.loc[2021, "Owner_Earnings"], 140.0)

    def test_negative_invested_capital_yields_infinite_roic(self):
        sample = make_sample_input()
        # Set short-term investments extremely high to drive Invested_Capital negative
        # total_equity(500) + debt(150) - short_term_investment(1000) = -350
        sample.financials.short_term_investment = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0]

        calculator = FinancialCalculator(sample, maintenance_capex_ratio=0.5)
        df = calculator.df

        # Invested capital must be negative
        self.assertLess(df.loc[2020, "Invested_Capital"], 0)
        # NOPAT is positive
        self.assertGreater(df.loc[2020, "NOPAT"], 0)
        # ROIC must be positive infinity
        self.assertEqual(df.loc[2020, "ROIC"], np.inf)


if __name__ == "__main__":
    unittest.main()
