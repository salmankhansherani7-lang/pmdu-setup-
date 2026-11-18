"""
Plotly Visualization Suite:
Designed with enterprise elegance, clean white/light styling,
crisp labels, soft gridlines, and high-readability values.
"""
from typing import Dict, Any, List, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Clean Light Modern Theme Layout
THEME_LAYOUT = dict(
    font=dict(family="Plus Jakarta Sans, Inter, -apple-system, sans-serif", color="#0F172A", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=30, r=30, t=45, b=30),
    xaxis=dict(
        showgrid=True,
        gridcolor="#F1F5F9",
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=11, color="#475569")
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#F1F5F9",
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=11, color="#475569")
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11, color="#475569")
    )
)

COLOR_SEQUENCE = ["#2563EB", "#0D9488", "#F59E0B", "#6366F1", "#8B5CF6", "#059669", "#EC4899", "#3B82F6"]

def create_bar_chart(
    data: Dict[str, Any],
    title: str = "",
    x_label: str = "",
    y_label: str = "Complaints Count",
    color: str = "#2563EB",
    horizontal: bool = False,
    is_percentage: bool = False
) -> go.Figure:
    """Creates a sleek, high-contrast, interactive bar chart with values on bars."""
    x_vals = list(data.keys())
    y_vals = list(data.values())

    text_template = [f"{v:.1f}%" if is_percentage else f"{v:,}" for v in y_vals]

    if horizontal:
        fig = go.Figure(go.Bar(
            x=y_vals,
            y=x_vals,
            orientation="h",
            marker=dict(color=color, cornerradius=4),
            text=text_template,
            textposition="outside",
            hovertemplate="<b>%{y}</b>: %{x}" + ("%" if is_percentage else "") + "<extra></extra>"
        ))
        fig.update_layout(
            **THEME_LAYOUT,
            title=dict(text=f"<b>{title}</b>", font=dict(size=14, color="#0F172A")),
            xaxis_title=y_label,
            yaxis_title=x_label
        )
    else:
        fig = go.Figure(go.Bar(
            x=x_vals,
            y=y_vals,
            marker=dict(color=color, cornerradius=4),
            text=text_template,
            textposition="outside",
            hovertemplate="<b>%{x}</b>: %{y}" + ("%" if is_percentage else "") + "<extra></extra>"
        ))
        fig.update_layout(
            **THEME_LAYOUT,
            title=dict(text=f"<b>{title}</b>", font=dict(size=14, color="#0F172A")),
            xaxis_title=x_label,
            yaxis_title=y_label
        )

    return fig

def create_donut_chart(
    data: Dict[str, Any],
    title: str = "",
    hole: float = 0.55
) -> go.Figure:
    """Creates a modern donut chart with clear labels and percentages."""
    labels = list(data.keys())
    values = list(data.values())

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker=dict(colors=COLOR_SEQUENCE),
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        textfont=dict(size=11, color="#1E293B")
    ))
    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color="#0F172A")),
        showlegend=False
    )
    return fig

def create_line_chart(
    data: Dict[str, Any],
    title: str = "",
    x_label: str = "Reporting Period",
    y_label: str = "Complaints Count"
) -> go.Figure:
    """Creates a multi-point trend line with markers and volume bars."""
    x_vals = list(data.keys())
    y_vals = list(data.values())

    fig = go.Figure()
    # Add subtle volume bars
    fig.add_trace(go.Bar(
        x=x_vals,
        y=y_vals,
        name="Monthly Volume",
        marker=dict(color="#E2E8F0", cornerradius=3),
        opacity=0.7,
        hovertemplate="<b>%{x}</b> Volume: %{y}<extra></extra>"
    ))
    # Add trend line
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        name="Trend Trajectory",
        mode="lines+markers",
        line=dict(color="#2563EB", width=3, shape="spline"),
        marker=dict(color="#0D9488", size=8, line=dict(color="#FFFFFF", width=2)),
        hovertemplate="<b>%{x}</b> Trend: %{y}<extra></extra>"
    ))
    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color="#0F172A")),
        xaxis_title=x_label,
        yaxis_title=y_label
    )
    return fig

def create_grouped_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: str,
    title: str = ""
) -> go.Figure:
    """Creates a grouped bar chart for multi-category comparisons."""
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=group_col,
        barmode="group",
        color_discrete_sequence=COLOR_SEQUENCE,
        title=f"<b>{title}</b>"
    )
    fig.update_layout(**THEME_LAYOUT)
    return fig
