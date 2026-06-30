import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from i18n import t


def create_waterfall_chart(waterfall_data: dict, start_year: int, end_year: int) -> go.Figure:
    x_labels = [
        t("chart.waterfall.label.ocf"),
        t("chart.waterfall.label.capex"),
        t("chart.waterfall.label.dividends"),
        t("chart.waterfall.label.buybacks"),
        t("chart.waterfall.label.ma"),
        t("chart.waterfall.label.other"),
    ]
    y_values = [
        waterfall_data["Total_Operating_Cash_Flow"],
        -waterfall_data["CapEx"],
        -waterfall_data["Dividends"],
        -waterfall_data["Buybacks"],
        -waterfall_data["M_and_A"],
        -waterfall_data["Other_Retention"],
    ]

    max_value = max(abs(value) for value in y_values)
    if max_value >= 1000:
        scale = 1000.0
        unit_label = t("chart.unit.billions")
        suffix = "B"
    else:
        scale = 1.0
        unit_label = t("chart.unit.millions")
        suffix = "M"

    measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    hover_texts = []
    for label, value, m in zip(x_labels, y_values, measure):
        sign = "+" if (m == "absolute" or value > 0) else "-"
        hover_texts.append(
            t("chart.waterfall.hover", label=label, sign=sign, amount=abs(value) / scale, suffix=suffix)
        )

    fig = go.Figure(
        go.Waterfall(
            name="Capital Flow",
            orientation="v",
            measure=measure,
            x=x_labels,
            textposition="outside",
            text=[f"{value / scale:.1f}{suffix}" for value in y_values],
            hovertext=hover_texts,
            hovertemplate="%{hovertext}<extra></extra>",
            y=y_values,
            connector={"line": {"color": "rgb(63, 63, 63)", "width": 1.5}},
            decreasing={"marker": {"color": "#ff4d4d"}},
            increasing={"marker": {"color": "#00ffcc"}},
            totals={"marker": {"color": "#3399ff"}},
        )
    )

    if start_year != end_year:
        title_text = t("chart.waterfall.title.cumulative", start_year=start_year, end_year=end_year, unit_label=unit_label)
    else:
        title_text = t("chart.waterfall.title.single", year=start_year, unit_label=unit_label)
    fig.update_layout(
        title=title_text,
        waterfallgap=0.3,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
    )
    return fig


def create_allocation_pie_chart(waterfall_data: dict) -> go.Figure:
    fig = px.pie(
        names=[
            t("chart.pie.label.capex"),
            t("chart.pie.label.dividends"),
            t("chart.pie.label.buybacks"),
            t("chart.pie.label.ma"),
            t("chart.pie.label.other"),
        ],
        values=[
            waterfall_data["CapEx"],
            waterfall_data["Dividends"],
            waterfall_data["Buybacks"],
            waterfall_data["M_and_A"],
            max(0, waterfall_data["Other_Retention"]),
        ],
        hole=0.4,
        color_discrete_sequence=["#10B981", "#3B82F6", "#EC4899", "#F59E0B", "#6B7280"],
    )
    fig.update_traces(marker=dict(line=dict(color="rgba(128, 128, 128, 1.0)", width=1.0)))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=350,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


def create_roic_chart(
    audited_df,
    roiic_retained_col_1: str,
    roiic_retained_col_2: str,
    roiic_window_1: int,
    roiic_window_2: int,
    roiic_retained_lag: int,
) -> go.Figure:
    plot_df = audited_df.copy()
    plot_df["ROIC"] = plot_df["ROIC"].replace([np.inf, -np.inf], np.nan)
    plot_df[roiic_retained_col_1] = plot_df[roiic_retained_col_1].replace([np.inf, -np.inf], np.nan)
    if roiic_retained_col_2 in plot_df.columns:
        plot_df[roiic_retained_col_2] = plot_df[roiic_retained_col_2].replace([np.inf, -np.inf], np.nan)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=plot_df.index,
            y=plot_df["ROIC"],
            mode="lines+markers",
            name=t("chart.roic.trace.roic"),
            line=dict(color="#10B981", width=3),
            marker=dict(size=8, color="#10B981"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=plot_df.index,
            y=plot_df[roiic_retained_col_1],
            mode="lines+markers",
            name=t("chart.roic.trace.roiic_retained", window=roiic_window_1, lag=roiic_retained_lag),
            line=dict(color="#3399ff", width=2, dash="dash"),
            marker=dict(size=6),
        )
    )

    if roiic_retained_col_2 != roiic_retained_col_1:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df[roiic_retained_col_2],
                mode="lines+markers",
                name=t("chart.roic.trace.roiic_retained", window=roiic_window_2, lag=roiic_retained_lag),
                line=dict(color="#ff9900", width=2.5, dash="dot"),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title=t("chart.roic.title"),
        xaxis_title=t("chart.xaxis.year"),
        yaxis_title=t("chart.roic.yaxis"),
        xaxis=dict(tickmode="linear", tick0=min(audited_df.index), dtick=1),
        yaxis=dict(tickformat=".1%"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def create_buyback_chart(display_df, market_currency: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=display_df.index,
            y=display_df["Intrinsic_Value_Share_Market_Currency"],
            mode="lines+markers",
            name=t("chart.buyback.trace.intrinsic"),
            line=dict(color="#10B981", width=3),
            marker=dict(size=8),
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=display_df.index,
            y=display_df["avg_stock_price"],
            mode="lines+markers",
            name=t("chart.buyback.trace.avg_price"),
            line=dict(color="#8892b0", width=1.5, dash="dash"),
            marker=dict(size=5),
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        )
    )

    buyback_active = display_df[display_df["Buyback_Price_Share_Market_Currency"] > 0]
    fig.add_trace(
        go.Scatter(
            x=buyback_active.index,
            y=buyback_active["Buyback_Price_Share_Market_Currency"],
            mode="markers",
            name=t("chart.buyback.trace.buyback_price"),
            marker=dict(color="#ff3366", size=12, symbol="triangle-up", line=dict(color="#ffffff", width=1.5)),
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=t("chart.buyback.title"),
        xaxis_title=t("chart.xaxis.year"),
        yaxis_title=t("chart.buyback.yaxis", currency=market_currency),
        yaxis=dict(tickformat=",.2f"),
        xaxis=dict(tickmode="linear", tick0=min(display_df.index), dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def create_ma_goodwill_chart(
    audited_df,
    acquisition_roiic_col_1: str,
    acquisition_roiic_col_2: str,
    roiic_window_1: int,
    roiic_window_2: int,
    roiic_retained_lag: int,
) -> go.Figure:
    plot_df = audited_df.copy()
    for col in [acquisition_roiic_col_1, acquisition_roiic_col_2]:
        if col in plot_df.columns:
            plot_df[col] = plot_df[col].replace([np.inf, -np.inf], np.nan)

    fig = go.Figure()

    if "Goodwill_to_Equity" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["Goodwill_to_Equity"],
                mode="lines+markers",
                name=t("chart.ma.trace.goodwill_to_equity"),
                line=dict(color="#F59E0B", width=2.5),
                marker=dict(size=7),
                hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
            )
        )

    if "ma_paid" in plot_df.columns:
        ma_values = plot_df["ma_paid"]
        max_value = float(ma_values.max()) if not ma_values.empty else 0.0
        scale, suffix = (1000.0, "B") if max_value >= 1000 else (1.0, "M")
        fig.add_trace(
            go.Bar(
                x=plot_df.index,
                y=ma_values / scale,
                name=t("chart.ma.trace.ma_spend", suffix=suffix),
                marker=dict(color="rgba(107, 114, 128, 0.35)"),
                yaxis="y2",
                hovertemplate="%{x}<br>%{y:.1f}" + suffix + "<extra></extra>",
            )
        )

    for col, color, dash, window in [
        (acquisition_roiic_col_1, "#3399ff", "dash", roiic_window_1),
        (acquisition_roiic_col_2, "#ff9900", "dot", roiic_window_2),
    ]:
        if col in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df[col],
                    mode="lines+markers",
                    name=t("chart.ma.trace.acquisition_roiic", window=window, lag=roiic_retained_lag),
                    line=dict(color=color, width=2, dash=dash),
                    marker=dict(size=6),
                    hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
                )
            )

    fig.update_layout(
        title=t("chart.ma.title"),
        xaxis_title=t("chart.xaxis.year"),
        yaxis=dict(title=t("chart.ma.yaxis"), tickformat=".1%"),
        yaxis2=dict(title=t("chart.ma.yaxis2"), overlaying="y", side="right", showgrid=False),
        xaxis=dict(tickmode="linear", tick0=min(plot_df.index), dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        barmode="group",
    )
    return fig


def create_earnings_quality_chart(audited_df) -> go.Figure:
    fig = go.Figure()

    max_value = 0.0
    for c in ["net_profit", "Owner_Earnings", "FCF"]:
        if c in audited_df.columns:
            vals = audited_df[c].dropna()
            if not vals.empty:
                max_value = max(max_value, float(vals.max()))
    scale, suffix = (1000.0, "B") if max_value >= 1000 else (1.0, "M")

    for col, name_key, color in [
        ("net_profit", "chart.eq.trace.net_profit", "#8892b0"),
        ("Owner_Earnings", "chart.eq.trace.owner_earnings", "#10B981"),
        ("FCF", "chart.eq.trace.fcf", "#3399ff"),
    ]:
        if col in audited_df.columns:
            fig.add_trace(
                go.Bar(
                    x=audited_df.index,
                    y=audited_df[col] / scale,
                    name=f"{t(name_key)} ({suffix})",
                    marker=dict(color=color),
                    hovertemplate="%{x}<br>%{y:.1f}" + suffix + "<extra></extra>",
                )
            )

    if "Accruals_Ratio" in audited_df.columns:
        fig.add_trace(
            go.Scatter(
                x=audited_df.index,
                y=audited_df["Accruals_Ratio"],
                mode="lines+markers",
                name=t("chart.eq.trace.accruals_ratio"),
                line=dict(color="#ff3366", width=2.5),
                marker=dict(size=8),
                yaxis="y2",
                hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
            )
        )

    fig.update_layout(
        title=t("chart.eq.title"),
        xaxis_title=t("chart.xaxis.year"),
        yaxis=dict(title=t("chart.eq.yaxis", suffix=suffix)),
        yaxis2=dict(title=t("chart.eq.yaxis2"), overlaying="y", side="right", tickformat=".1%", showgrid=False),
        xaxis=dict(tickmode="linear", tick0=min(audited_df.index), dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        barmode="group",
    )
    return fig
