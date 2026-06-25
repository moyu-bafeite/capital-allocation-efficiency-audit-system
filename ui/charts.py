import plotly.express as px
import plotly.graph_objects as go


def create_waterfall_chart(waterfall_data: dict, start_year: int, end_year: int) -> go.Figure:
    x_labels = ["经营现金流（总流入）", "资本支出 (CapEx)", "现金分红", "股份回购", "投资与并购", "其他现金 / 债务留存"]
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
        unit_label = "Billions"
        suffix = "B"
    else:
        scale = 1.0
        unit_label = "Millions"
        suffix = "M"

    measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    hover_texts = []
    for label, value, m in zip(x_labels, y_values, measure):
        sign = "+" if (m == "absolute" or value > 0) else "-"
        hover_texts.append(f"{label}<br>金额: {sign}{abs(value) / scale:.1f}{suffix}")

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

    title_text = (
        f"{start_year} - {end_year} 年累计资本分配去向瀑布图（单位：{unit_label}）"
        if start_year != end_year
        else f"{start_year} 年度单年资本分配去向瀑布图（单位：{unit_label}）"
    )
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
        names=["资本支出 (CapEx)", "现金分红", "股份回购", "投资并购", "其他现金 / 债务留存"],
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
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=audited_df.index,
            y=audited_df["ROIC"],
            mode="lines+markers",
            name="ROIC（存量回报率）",
            line=dict(color="#10B981", width=3),
            marker=dict(size=8, color="#10B981"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=audited_df.index,
            y=audited_df[roiic_retained_col_1],
            mode="lines+markers",
            name=f"ROIIC Retained（{roiic_window_1} 年滚动增量，滞后 {roiic_retained_lag} 年）",
            line=dict(color="#3399ff", width=2, dash="dash"),
            marker=dict(size=6),
        )
    )

    if roiic_retained_col_2 != roiic_retained_col_1:
        fig.add_trace(
            go.Scatter(
                x=audited_df.index,
                y=audited_df[roiic_retained_col_2],
                mode="lines+markers",
                name=f"ROIIC Retained（{roiic_window_2} 年滚动增量，滞后 {roiic_retained_lag} 年）",
                line=dict(color="#ff9900", width=2.5, dash="dot"),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title="ROIC 与 ROIIC（留存盈余视角）趋势",
        xaxis_title="年份",
        yaxis_title="回报率",
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
            name="保守每股内在价值（折算为市场币种）",
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
            name="年平均交易股价",
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
            name="实际股份回购均价",
            marker=dict(color="#ff3366", size=12, symbol="triangle-up", line=dict(color="#ffffff", width=1.5)),
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="每股内在价值（估值锚）vs. 年度均价 vs. 实际回购成交价",
        xaxis_title="年份",
        yaxis_title=f"价格 ({market_currency})",
        yaxis=dict(tickformat=",.2f"),
        xaxis=dict(tickmode="linear", tick0=min(display_df.index), dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
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
    fig = go.Figure()

    # Left axis: goodwill-to-equity ratio (percent)
    if "Goodwill_to_Equity" in audited_df.columns:
        fig.add_trace(
            go.Scatter(
                x=audited_df.index,
                y=audited_df["Goodwill_to_Equity"],
                mode="lines+markers",
                name="商誉 / 股东权益",
                line=dict(color="#F59E0B", width=2.5),
                marker=dict(size=7),
                hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
            )
        )

    # Right axis: M&A cash spend as bars
    if "ma_paid" in audited_df.columns:
        ma_values = audited_df["ma_paid"]
        max_value = float(ma_values.max()) if not ma_values.empty else 0.0
        scale, suffix = (1000.0, "B") if max_value >= 1000 else (1.0, "M")
        fig.add_trace(
            go.Bar(
                x=audited_df.index,
                y=ma_values / scale,
                name=f"并购现金支出 ({suffix})",
                marker=dict(color="rgba(107, 114, 128, 0.35)"),
                yaxis="y2",
                hovertemplate="%{x}<br>%{y:.1f}" + suffix + "<extra></extra>",
            )
        )

    # Acquisition ROIIC lines (left axis, percent)
    for col, color, dash, window in [
        (acquisition_roiic_col_1, "#3399ff", "dash", roiic_window_1),
        (acquisition_roiic_col_2, "#ff9900", "dot", roiic_window_2),
    ]:
        if col in audited_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=audited_df.index,
                    y=audited_df[col],
                    mode="lines+markers",
                    name=f"Acquisition ROIIC（{window} 年滚动，滞后 {roiic_retained_lag} 年）",
                    line=dict(color=color, width=2, dash=dash),
                    marker=dict(size=6),
                    hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
                )
            )

    fig.update_layout(
        title="商誉占比、并购支出与并购资本回报率",
        xaxis_title="年份",
        yaxis=dict(title="回报率 / 占比", tickformat=".1%"),
        yaxis2=dict(title="并购支出", overlaying="y", side="right", showgrid=False),
        xaxis=dict(tickmode="linear", tick0=min(audited_df.index), dtick=1),
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

    # Determine amount scale across the three earnings series
    max_value = 0.0
    for c in ["net_profit", "Owner_Earnings", "FCF"]:
        if c in audited_df.columns:
            vals = audited_df[c].dropna()
            if not vals.empty:
                max_value = max(max_value, float(vals.max()))
    scale, suffix = (1000.0, "B") if max_value >= 1000 else (1.0, "M")

    # Grouped bars: net profit / owner earnings / FCF
    for col, name, color in [
        ("net_profit", "净利润", "#8892b0"),
        ("Owner_Earnings", "所有者盈余", "#10B981"),
        ("FCF", "自由现金流", "#3399ff"),
    ]:
        if col in audited_df.columns:
            fig.add_trace(
                go.Bar(
                    x=audited_df.index,
                    y=audited_df[col] / scale,
                    name=f"{name} ({suffix})",
                    marker=dict(color=color),
                    hovertemplate="%{x}<br>%{y:.1f}" + suffix + "<extra></extra>",
                )
            )

    # Right axis: accruals ratio trend
    if "Accruals_Ratio" in audited_df.columns:
        fig.add_trace(
            go.Scatter(
                x=audited_df.index,
                y=audited_df["Accruals_Ratio"],
                mode="lines+markers",
                name="应计项比率",
                line=dict(color="#ff3366", width=2.5),
                marker=dict(size=8),
                yaxis="y2",
                hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
            )
        )

    fig.update_layout(
        title="净利润 vs 所有者盈余 vs 自由现金流（含应计项比率）",
        xaxis_title="年份",
        yaxis=dict(title=f"金额 ({suffix})"),
        yaxis2=dict(title="应计项比率", overlaying="y", side="right", tickformat=".1%", showgrid=False),
        xaxis=dict(tickmode="linear", tick0=min(audited_df.index), dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier Prime"),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        barmode="group",
    )
    return fig
