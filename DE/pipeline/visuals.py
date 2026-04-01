"""
pipeline/visuals.py

Plotly chart functions for the PlayerData Streamlit dashboard.
Each function accepts a pre-filtered / pre-computed dataframe and returns
a plotly.graph_objects.Figure that the app can render with st.plotly_chart().

Charts are grouped by audience:
  - Overview    : summary stats across the filtered cohort
  - Age Group   : the DS-team metric comparisons across age brackets
  - Athlete     : individual drilldown (single athlete across sessions)
  - Sport/Div   : cross-sport or cross-division benchmarks
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Shared palette / helpers
# ---------------------------------------------------------------------------

_PALETTE = px.colors.qualitative.Bold
_BG = "#0e1117"
_PAPER = "#1a1d27"
_GRID = "#2d3043"
_TEXT = "#ffffff"

_BASE_LAYOUT = dict(
    paper_bgcolor=_PAPER,
    plot_bgcolor=_BG,
    font=dict(color=_TEXT, family="Inter, Arial, sans-serif", size=13),
    xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID, tickfont=dict(color=_TEXT)),
    yaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID, tickfont=dict(color=_TEXT)),
    legend=dict(
        font=dict(color=_TEXT, size=13),
        bgcolor="rgba(0,0,0,0)",
        bordercolor=_GRID,
        borderwidth=1,
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(l=50, r=30, t=50, b=90),
)

# Map raw snake_case category values to readable display labels
_LABEL_ALIASES = {
    "association_football": "Association Football",
    "american_football":    "American Football",
    "male":   "Male",
    "female": "Female",
    "di":     "DI",
    "dii":    "DII",
    "diii":   "DIII",
}


def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=_TEXT)),
        **_BASE_LAYOUT,
    )
    # Rename legend entries using labelalias (Plotly 5.13+) and fallback rename
    fig.update_layout(newshape=dict())  # no-op to ensure layout object exists
    try:
        fig.update_layout(legend=dict(
            font=dict(color=_TEXT, size=13),
            bgcolor="rgba(0,0,0,0)",
        ))
        fig.for_each_trace(lambda t: t.update(
            name=_LABEL_ALIASES.get(t.name, t.name.replace("_", " ").title())
            if t.name else t.name
        ))
    except Exception:
        pass
    return fig


# ---------------------------------------------------------------------------
# 1. Session Load Distribution
# ---------------------------------------------------------------------------


def plot_session_load_distribution(
    df: pd.DataFrame,
    group_by: str = "athlete_sport",
    title: str = "Session Load Distribution",
) -> go.Figure:
    """
    Box + strip chart of session_load, coloured by group_by column.
    Useful for coaches to see load spread across sports or age groups.
    """
    fig = px.box(
        df,
        x=group_by,
        y="session_load",
        color=group_by,
        points="outliers",
        color_discrete_sequence=_PALETTE,
        labels={group_by: group_by.replace("_", " ").title(), "session_load": "Session Load"},
    )
    fig.update_traces(boxmean="sd")
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 2. Speed Profile  (avg vs max scatter)
# ---------------------------------------------------------------------------


def plot_speed_profile(
    df: pd.DataFrame,
    color_by: str = "athlete_sport",
    title: str = "Speed Profile: Avg vs Max Speed",
) -> go.Figure:
    """
    Scatter of avg_speed_kph vs max_speed_kph, coloured by group.
    Diagonal reference line shows where avg == max (upper bound).
    Athletes above the diagonal are impossible – useful data quality check.
    """
    fig = px.scatter(
        df,
        x="avg_speed_kph",
        y="max_speed_kph",
        color=color_by,
        opacity=0.65,
        color_discrete_sequence=_PALETTE,
        hover_data=["athlete_number", "athlete_relative_age", "active_minutes"],
        labels={
            "avg_speed_kph":  "Avg Speed (kph)",
            "max_speed_kph":  "Max Speed (kph)",
            color_by: color_by.replace("_", " ").title(),
        },
    )
    # reference line avg == max
    max_val = float(df["max_speed_kph"].max()) if not df.empty else 40
    fig.add_shape(
        type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="#ff6b6b", dash="dash", width=1),
    )
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 3. Distance Breakdown  (total / high-intensity / sprint)
# ---------------------------------------------------------------------------


def plot_distance_breakdown(
    df: pd.DataFrame,
    group_col: str = "athlete_sport",
    title: str = "Average Distance Breakdown by Group",
) -> go.Figure:
    """
    Grouped bar chart showing mean total, high-intensity, and sprint
    distance for each value of group_col.
    """
    agg = (
        df.groupby(group_col)[
            ["total_distance_m", "total_high_intensity_distance_m", "total_sprint_distance_m"]
        ]
        .mean()
        .reset_index()
        .round(1)
    )

    fig = go.Figure()
    bars = {
        "total_distance_m":                    "Total Distance",
        "total_high_intensity_distance_m":     "High Intensity",
        "total_sprint_distance_m":             "Sprint",
    }
    colours = ["#4cc9f0", "#f72585", "#7209b7"]
    for (col, label), colour in zip(bars.items(), colours):
        fig.add_bar(
            x=agg[group_col],
            y=agg[col],
            name=label,
            marker_color=colour,
        )

    fig.update_layout(barmode="group")
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 4. Age-Group Summary  (from compute_age_group_summary)
# ---------------------------------------------------------------------------


def plot_age_group_summary(
    summary_df: pd.DataFrame,
    metric: str = "total_distance_m",
    title: Optional[str] = None,
) -> go.Figure:
    """
    Line chart with error-band (mean ± sd) and 10th/90th percentile markers
    across age groups.  Uses the summary_df returned by metrics.compute_age_group_summary().
    """
    if title is None:
        title = f"{metric.replace('_', ' ').title()} by Age Group"

    avg_col    = f"avg_{metric}"
    sd_col     = f"sd_{metric}"
    top_col    = f"top10_{metric}"
    bottom_col = f"bottom10_{metric}"

    missing = [c for c in [avg_col, sd_col, top_col, bottom_col] if c not in summary_df.columns]
    if missing:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data for this view", showarrow=False)
        return _apply_base(fig, title)

    sd = summary_df[sd_col].fillna(0)
    upper = summary_df[avg_col] + sd
    lower = (summary_df[avg_col] - sd).clip(lower=0)

    fig = go.Figure()

    # SD band
    fig.add_trace(go.Scatter(
        x=pd.concat([summary_df["athlete_relative_age"], summary_df["athlete_relative_age"][::-1]]),
        y=pd.concat([upper, lower[::-1]]),
        fill="toself",
        fillcolor="rgba(76,201,240,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="±1 SD",
        showlegend=True,
    ))

    # Mean line
    fig.add_trace(go.Scatter(
        x=summary_df["athlete_relative_age"],
        y=summary_df[avg_col],
        mode="lines+markers",
        name="Mean",
        line=dict(color="#4cc9f0", width=2),
        marker=dict(size=6),
    ))

    # 90th pctile
    fig.add_trace(go.Scatter(
        x=summary_df["athlete_relative_age"],
        y=summary_df[top_col],
        mode="lines",
        name="90th Pctile",
        line=dict(color="#f72585", dash="dot", width=1.5),
    ))

    # 10th pctile
    fig.add_trace(go.Scatter(
        x=summary_df["athlete_relative_age"],
        y=summary_df[bottom_col],
        mode="lines",
        name="10th Pctile",
        line=dict(color="#7209b7", dash="dot", width=1.5),
    ))

    fig.update_layout(xaxis_title="Age", yaxis_title=metric.replace("_", " ").title())
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 5. Percentile Ranking Radar  (individual athlete vs age-group peers)
# ---------------------------------------------------------------------------


def plot_percentile_radar(
    athlete_row: pd.Series,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Radar / spider chart showing an athlete's percentile rank for the three
    DS-team metrics vs their age-group peers.
    Expects columns: total_dist_perc_rank, max_speed_perc_rank, session_load_perc_rank.
    """
    rank_cols = {
        "total_dist_perc_rank":   "Distance",
        "max_speed_perc_rank":    "Max Speed",
        "session_load_perc_rank": "Session Load",
    }

    missing = [c for c in rank_cols if c not in athlete_row.index]
    if missing:
        fig = go.Figure()
        fig.add_annotation(text="Rank columns not available", showarrow=False)
        return _apply_base(fig, title or "Percentile Radar")

    categories = list(rank_cols.values())
    values     = [float(athlete_row[c]) for c in rank_cols]
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    title = title or f"Athlete #{int(athlete_row.get('athlete_number', 0))} – Percentile Ranks"

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(247,37,133,0.25)",
        line=dict(color="#f72585", width=2),
        name="Percentile",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=_BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=_GRID, tickcolor=_TEXT,
                tickfont=dict(color=_TEXT),
            ),
            angularaxis=dict(gridcolor=_GRID, tickcolor=_TEXT, tickfont=dict(color=_TEXT)),
        ),
        showlegend=False,
    )
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 6. Volume vs Intensity Scatter
# ---------------------------------------------------------------------------


def plot_volume_vs_intensity(
    df: pd.DataFrame,
    color_by: str = "athlete_sport",
    title: str = "Volume vs Intensity",
) -> go.Figure:
    """
    active_minutes (volume proxy) on X, session_load (intensity proxy) on Y.
    Bubble size = total_distance_m.
    """
    fig = px.scatter(
        df,
        x="active_minutes",
        y="session_load",
        color=color_by,
        size="total_distance_m",
        size_max=18,
        opacity=0.65,
        color_discrete_sequence=_PALETTE,
        hover_data=["athlete_number", "athlete_relative_age", "max_speed_kph"],
        labels={
            "active_minutes": "Active Minutes",
            "session_load":   "Session Load",
            color_by: color_by.replace("_", " ").title(),
        },
    )
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 7. Acceleration / Deceleration Heatmap
# ---------------------------------------------------------------------------


def plot_accel_decel_heatmap(
    df: pd.DataFrame,
    group_col: str = "athlete_sport",
    title: str = "Avg Acceleration & Deceleration Events by Group",
) -> go.Figure:
    """
    Grouped horizontal bar chart: avg acceleration_events and
    deceleration_events per group.
    """
    agg = (
        df.groupby(group_col)[["acceleration_events", "deceleration_events"]]
        .mean()
        .reset_index()
        .round(1)
    )

    fig = go.Figure()
    fig.add_bar(
        y=agg[group_col], x=agg["acceleration_events"],
        name="Accel Events", orientation="h", marker_color="#4cc9f0",
    )
    fig.add_bar(
        y=agg[group_col], x=-agg["deceleration_events"],
        name="Decel Events", orientation="h", marker_color="#f72585",
    )

    fig.update_layout(
        barmode="overlay",
        xaxis_title="Events (positive = accel, negative = decel)",
        yaxis_title=group_col.replace("_", " ").title(),
    )
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 8. Individual Athlete Multi-Session Summary
# ---------------------------------------------------------------------------


def plot_athlete_sessions(
    athlete_df: pd.DataFrame,
    athlete_id: int,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Line / bar charts for a single athlete across all their sessions.
    Shows session_load, total_distance_m, and max_speed_kph side by side.
    """
    rows = athlete_df[athlete_df["athlete_number"] == athlete_id].copy()
    rows = rows.reset_index(drop=True)
    rows["session"] = [f"S{i+1}" for i in range(len(rows))]

    title = title or f"Athlete #{athlete_id} – Session History"

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        subplot_titles=["Session Load", "Total Distance (m)", "Max Speed (kph)"],
        vertical_spacing=0.08,
    )

    colour_map = ["#4cc9f0", "#f72585", "#7209b7"]
    metrics    = ["session_load", "total_distance_m", "max_speed_kph"]

    for i, (metric, colour) in enumerate(zip(metrics, colour_map), start=1):
        if metric not in rows.columns:
            continue
        fig.add_trace(
            go.Bar(x=rows["session"], y=rows[metric], marker_color=colour, name=metric),
            row=i, col=1,
        )

    fig.update_layout(showlegend=False, height=520)
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 9. Sport Benchmark Heatmap
# ---------------------------------------------------------------------------


def plot_sport_benchmark_heatmap(
    df: pd.DataFrame,
    title: str = "Sport Benchmark – Mean Performance Metrics",
) -> go.Figure:
    """
    Heatmap of normalised (0-1) mean metrics per sport.
    Allows quick cross-sport comparison for coaches.
    """
    metrics = [
        "total_distance_m", "max_speed_kph", "session_load",
        "metres_per_minute", "high_intensity_events", "sprint_events",
    ]
    available = [m for m in metrics if m in df.columns]

    agg = df.groupby("athlete_sport")[available].mean().round(2)
    normalised = (agg - agg.min()) / (agg.max() - agg.min() + 1e-9)

    fig = go.Figure(go.Heatmap(
        z=normalised.values,
        x=[c.replace("_", " ").title() for c in normalised.columns],
        y=normalised.index.tolist(),
        colorscale="Plasma",
        text=agg.to_numpy(dtype=float, na_value=0.0).round(1),
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(tickfont=dict(color=_TEXT)),
    ))

    fig.update_layout(
        xaxis_tickangle=-30,
        yaxis_title="Sport",
    )
    return _apply_base(fig, title)


# ---------------------------------------------------------------------------
# 10. Age vs Metric Scatter with Trendline
# ---------------------------------------------------------------------------


def plot_age_metric_scatter(
    df: pd.DataFrame,
    metric: str = "total_distance_m",
    color_by: str = "athlete_gender_marker",
    title: Optional[str] = None,
) -> go.Figure:
    """
    Scatter of athlete_relative_age vs a chosen metric with OLS trendline.
    Useful to identify age-related performance curves.
    """
    if title is None:
        title = f"Age vs {metric.replace('_', ' ').title()}"

    fig = px.scatter(
        df,
        x="athlete_relative_age",
        y=metric,
        color=color_by,
        trendline="ols",
        opacity=0.5,
        color_discrete_sequence=_PALETTE,
        hover_data=["athlete_number", "athlete_sport"],
        labels={
            "athlete_relative_age": "Age",
            metric: metric.replace("_", " ").title(),
            color_by: color_by.replace("_", " ").title(),
        },
    )
    return _apply_base(fig, title)
