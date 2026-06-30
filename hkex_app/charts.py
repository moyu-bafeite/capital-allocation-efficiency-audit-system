"""Plotly charts for the HKEX workbench.

Self-contained (does not reuse ``services/charts.py``, which is audit-specific).
"""
import pandas as pd
import plotly.graph_objects as go

from hkex_app.i18n import t


def trend_chart(df: pd.DataFrame, stock_code: str, company_name: str = "") -> go.Figure:
    """Single-ticker trend: three lines (excl. treasury / treasury / total)
    over report_period_date."""
    fig = go.Figure()
    name_part = f" ({company_name})" if company_name else ""
    title = t("hkex.chart.trend_title", stock=stock_code) + name_part

    if df.empty:
        fig.update_layout(
            title=title, template="plotly_white", height=450,
            xaxis_title=t("hkex.chart.axis.date"),
            yaxis_title=t("hkex.chart.axis.shares"),
        )
        return fig

    x = df["report_period_date"]

    def _line(y_col: str, legend_key: str, color: str, dash: str = "solid") -> None:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df[y_col],
                mode="lines+markers",
                name=t(legend_key),
                line={"color": color, "width": 2, "dash": dash},
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f}<extra></extra>",
            )
        )

    _line("shares_issued_excl_treasury", "hkex.chart.legend.issued_excl_treasury", "#1f77b4")
    _line("shares_treasury", "hkex.chart.legend.treasury", "#ff7f0e", dash="dot")
    _line("shares_total_issued", "hkex.chart.legend.total_issued", "#2ca02c")

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=450,
        xaxis_title=t("hkex.chart.axis.date"),
        yaxis_title=t("hkex.chart.axis.shares"),
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.2},
    )
    return fig


def compare_chart(df: pd.DataFrame, normalized: bool) -> go.Figure:
    """Multi-ticker comparison of total issued shares over time. When
    ``normalized`` is True, each ticker's first value is scaled to 100."""
    title = t("hkex.chart.compare_title")
    if normalized:
        title += " · " + t("hkex.chart.normalized_title")

    fig = go.Figure()
    if df.empty:
        fig.update_layout(
            title=title, template="plotly_white", height=450,
            xaxis_title=t("hkex.chart.axis.date"),
            yaxis_title=t("hkex.chart.axis.shares"),
        )
        return fig

    plot_df = df.copy()
    if normalized:
        plot_df = plot_df.sort_values(["ticker", "report_period_date"])
        first = plot_df.groupby("ticker")["shares_total_issued"].transform("first")
        plot_df["value"] = plot_df["shares_total_issued"] / first * 100.0
        y_col = "value"
    else:
        y_col = "shares_total_issued"

    for ticker, sub in plot_df.groupby("ticker"):
        sub = sub.sort_values("report_period_date")
        fig.add_trace(
            go.Scatter(
                x=sub["report_period_date"],
                y=sub[y_col],
                mode="lines+markers",
                name=ticker,
                line={"width": 2},
                hovertemplate=f"{ticker}<br>%{{x|%Y-%m-%d}}<br>%{{y:,.2f}}"
                               if normalized else f"{ticker}<br>%{{x|%Y-%m-%d}}<br>%{{y:,.0f}}"
                               + "<extra></extra>",
            )
        )

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=450,
        xaxis_title=t("hkex.chart.axis.date"),
        yaxis_title=(
            t("hkex.chart.axis.index") if normalized else t("hkex.chart.axis.shares")
        ),
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.2},
    )
    return fig
