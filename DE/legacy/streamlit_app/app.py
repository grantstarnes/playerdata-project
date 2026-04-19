"""
DE/app/app.py

PlayerData Analytics Dashboard
================================
Streamlit app with sidebar filters (gender / sport / division / age / active
minutes / data source) and four tabbed views:

  Overview        - cohort-level KPIs and summary charts
  Age Group       - DS-team metric comparisons across age brackets
  Athlete         - individual athlete drilldown
  Benchmarks      - cross-sport / cross-division comparison
  Chat            - rule-based natural language Q&A

Run from DE/ with:
    streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make DE/ importable regardless of CWD
_DE_ROOT = Path(__file__).resolve().parents[1]
if str(_DE_ROOT) not in sys.path:
    sys.path.insert(0, str(_DE_ROOT))

# Make DE/app/ importable so agent.py can be imported without triggering its UI
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import pandas as pd
import streamlit as st

from agent import _dispatch, _HELP_TEXT

from pipeline.metrics import (
    load_all_data,
    build_athlete_metrics,
    filter_sessions,
    PERF_METRICS,
)
from pipeline import visuals as viz

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PlayerData Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS overrides — PlayerData design tokens
# ---------------------------------------------------------------------------

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    :root {
      --pd-green:     #38D830;
      --pd-green-600: #2BB823;
      --pd-green-700: #1F9A19;
      --pd-green-50:  #E8FAE6;
      --pd-black:     #0A0A0A;
      --pd-ink-900:   #111418;
      --pd-ink-700:   #2A2F36;
      --pd-ink-500:   #4B5563;
      --pd-ink-400:   #6B7280;
      --pd-ink-300:   #9CA3AF;
      --pd-ink-200:   #D1D5DB;
      --pd-ink-100:   #E5E7EA;
      --pd-ink-50:    #F0F2F4;
      --pd-bg:        #F5F6F7;
      --pd-surface:   #FFFFFF;
      --status-error: #E5484D;
      --r-md: 10px;
      --r-lg: 14px;
      --shadow-xs: 0 1px 2px rgba(10,10,10,0.04);
      --shadow-sm: 0 2px 8px rgba(10,10,10,0.06);
      --font-display: 'Archivo', ui-sans-serif, system-ui, sans-serif;
      --font-body:    'Inter', ui-sans-serif, system-ui, sans-serif;
      --font-mono:    'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    /* App surface */
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
      background: var(--pd-bg) !important;
      color: var(--pd-black);
      font-family: var(--font-body);
      font-feature-settings: "ss01", "cv11";
    }
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }

    /* Typography */
    h1, h2, h3 { font-family: var(--font-display); letter-spacing: -0.015em; color: var(--pd-black); }
    h1 { font-weight: 700; font-size: 32px; line-height: 1.12; }
    h2 { font-weight: 700; font-size: 24px; line-height: 1.18; }
    h3 { font-weight: 600; font-size: 18px; line-height: 1.25; }
    p, label, span, div { color: var(--pd-ink-700); }
    code { font-family: var(--font-mono); font-size: 12.5px;
           background: var(--pd-ink-50); color: var(--pd-ink-700);
           padding: 1px 6px; border-radius: 6px; }

    /* Tabular numbers everywhere numbers live */
    .pd-kpi, .pd-kpi-delta, th, td, [data-testid="stMetricValue"] {
      font-variant-numeric: tabular-nums;
    }

    /* KPI card — matches .pd-card + .pd-kpi from the mockup */
    .pd-kpi-card {
      background: var(--pd-surface);
      border: 1px solid var(--pd-ink-100);
      border-radius: var(--r-lg);
      box-shadow: var(--shadow-xs);
      padding: 20px 22px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-height: 128px;
    }
    .pd-kpi-label {
      font-family: var(--font-body);
      font-weight: 600;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--pd-ink-400);
    }
    .pd-kpi {
      font-family: var(--font-display);
      font-weight: 700;
      font-size: 44px;
      line-height: 1.02;
      letter-spacing: -0.03em;
      color: var(--pd-black);
    }
    .pd-kpi-unit {
      font-family: var(--font-body);
      font-weight: 500;
      font-size: 12px;
      color: var(--pd-ink-400);
      margin-left: 4px;
    }
    .pd-kpi-delta {
      font-size: 12px;
      font-weight: 500;
      color: var(--pd-ink-400);
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .pd-kpi-delta.up    { color: var(--pd-green-700); }
    .pd-kpi-delta.down  { color: var(--status-error); }
    .pd-kpi-delta.flat  { color: var(--pd-ink-400); }

    /* Chart card — streamlit's st.container(border=True) gets a subtle re-style */
    [data-testid="stVerticalBlockBorderWrapper"] {
      background: var(--pd-surface);
      border: 1px solid var(--pd-ink-100) !important;
      border-radius: var(--r-lg) !important;
      box-shadow: var(--shadow-xs);
    }
    .pd-card-title {
      font-family: var(--font-display);
      font-weight: 600;
      font-size: 16px;
      color: var(--pd-black);
      margin: 0 0 2px;
    }
    .pd-card-sub {
      font-size: 12px;
      color: var(--pd-ink-400);
      margin: 0 0 10px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
      background: var(--pd-surface);
      border-right: 1px solid var(--pd-ink-100);
    }
    [data-testid="stSidebar"] h1 { font-size: 20px; margin-bottom: 0; }

    /* Streamlit tabs — pill-ish, with green active indicator */
    .stTabs [data-baseweb="tab-list"] {
      gap: 4px;
      border-bottom: 1px solid var(--pd-ink-100);
    }
    .stTabs [data-baseweb="tab"] {
      font-family: var(--font-body);
      font-weight: 600;
      font-size: 13px;
      color: var(--pd-ink-400);
      padding: 10px 14px;
    }
    .stTabs [aria-selected="true"] { color: var(--pd-black) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background: var(--pd-green) !important; height: 2px; }

    /* Buttons */
    .stButton > button {
      font-family: var(--font-body);
      font-weight: 600;
      border-radius: var(--r-md);
      border: 1px solid var(--pd-ink-200);
      background: var(--pd-surface);
      color: var(--pd-black);
      height: 36px;
    }
    .stButton > button:hover { background: var(--pd-ink-50); border-color: var(--pd-ink-200); }
    .stButton > button[kind="primary"] {
      background: var(--pd-green);
      color: var(--pd-black);
      border-color: var(--pd-green);
    }
    .stButton > button[kind="primary"]:hover { background: var(--pd-green-600); }

    /* Tables */
    [data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }

    /* Chat bubbles */
    [data-testid="stChatMessage"] {
      background: var(--pd-surface);
      border: 1px solid var(--pd-ink-100);
      border-radius: var(--r-lg);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading data…")
def get_data(include_synthetic: bool) -> pd.DataFrame:
    return load_all_data(include_synthetic=include_synthetic)


# ---------------------------------------------------------------------------
# Sidebar - Filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("PlayerData")
    st.caption("Analytics Dashboard")
    st.divider()

    st.subheader("Data Source")
    data_source = st.radio(
        "Include synthetic data?",
        options=["Sample + Synthetic", "Sample only", "Synthetic only"],
        index=0,
    )

    # Load appropriate dataset
    if data_source == "Sample only":
        raw_df = get_data(include_synthetic=False)
    else:
        raw_df = get_data(include_synthetic=True)

    if data_source == "Synthetic only":
        raw_df = raw_df[raw_df["athlete_number"] >= 1000].copy()

    st.divider()
    st.subheader("Filters")

    # Gender
    genders = sorted(raw_df["athlete_gender_marker"].dropna().unique().tolist())
    gender_labels = {g: g.title() for g in genders}
    selected_gender = st.selectbox(
        "Gender",
        options=["All"] + genders,
        format_func=lambda g: "All" if g == "All" else gender_labels.get(g, g),
    )

    # Sport
    sports = sorted(raw_df["athlete_sport"].dropna().unique().tolist())
    selected_sports = st.multiselect(
        "Sport",
        options=sports,
        default=sports,
        format_func=lambda s: s.replace("_", " ").title(),
    )

    # Division
    divisions = sorted(raw_df["club_division"].dropna().unique().tolist())
    selected_divisions = st.multiselect(
        "Division",
        options=divisions,
        default=divisions,
    )

    # Age range
    age_min = int(raw_df["athlete_relative_age"].min())
    age_max = int(raw_df["athlete_relative_age"].max())
    age_range = st.slider("Age Range", age_min, age_max, (age_min, age_max))

    # Min active minutes (DS default = 70)
    min_minutes = st.slider("Min Active Minutes", 0, 120, 70, step=5)

    st.divider()
    st.caption("Filters apply to all tabs except where noted.")


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    mask = (
        df["athlete_relative_age"].between(age_range[0], age_range[1])
        & df["athlete_sport"].isin(selected_sports if selected_sports else sports)
        & df["club_division"].isin(selected_divisions if selected_divisions else divisions)
        & (df["active_minutes"] >= min_minutes)
    )
    if selected_gender != "All":
        mask &= df["athlete_gender_marker"] == selected_gender
    return df[mask].copy()


filtered_df = apply_filters(raw_df)

# Build DS metrics on the filtered set
_gender_arg = None if selected_gender == "All" else selected_gender
athlete_df, summary_df = build_athlete_metrics(
    filtered_df,
    sport=None,       # sport already applied in apply_filters
    gender=None,      # gender already applied
    min_active_minutes=min_minutes,
)


# ---------------------------------------------------------------------------
# Helpers — KPI card + ChartCard
# ---------------------------------------------------------------------------

from contextlib import contextmanager

_DELTA_GLYPH = {"up": "↑", "down": "↓", "flat": "·"}

def _kpi(
    container,
    label: str,
    value: str,
    unit: str = "",
    delta: str = "",
    delta_dir: str = "flat",
) -> None:
    unit_html = f'<span class="pd-kpi-unit">{unit}</span>' if unit else ""
    delta_html = (
        f'<div class="pd-kpi-delta {delta_dir}">'
        f'{_DELTA_GLYPH.get(delta_dir, "")} {delta}</div>'
        if delta else '<div class="pd-kpi-delta flat">&nbsp;</div>'
    )
    container.markdown(
        f"""<div class="pd-kpi-card">
              <div class="pd-kpi-label">{label}</div>
              <div class="pd-kpi">{value}{unit_html}</div>
              {delta_html}
            </div>""",
        unsafe_allow_html=True,
    )


@contextmanager
def chart_card(title: str, subtitle: str = ""):
    """Bordered container with a Plotly-friendly title/subtitle header."""
    with st.container(border=True):
        sub_html = f'<div class="pd-card-sub">{subtitle}</div>' if subtitle else ""
        st.markdown(
            f'<div class="pd-card-title">{title}</div>{sub_html}',
            unsafe_allow_html=True,
        )
        yield


# ---------------------------------------------------------------------------
# Header — title + action row
# ---------------------------------------------------------------------------

hdr_left, hdr_right = st.columns([3, 2])
with hdr_left:
    st.markdown(
        '<h1 style="margin:0">Team Overview</h1>'
        f'<div style="color:var(--pd-ink-400); margin-top:6px; font-size:13px;">'
        f'{len(selected_sports)} sports · {"/".join(selected_divisions) or "—"} · '
        f'ages {age_range[0]}–{age_range[1]} · min {min_minutes} min'
        f'</div>',
        unsafe_allow_html=True,
    )
with hdr_right:
    a1, a2, a3 = st.columns(3)
    a1.button("📅 Last 30 days", use_container_width=True, key="hdr_range")
    a2.download_button(
        "⭳ Export",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="playerdata_filtered.csv",
        mime="text/csv",
        use_container_width=True,
        key="hdr_export",
    )
    a3.button("+ New session", type="primary", use_container_width=True, key="hdr_new")

st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

# KPI strip
col_h1, col_h2, col_h3, col_h4 = st.columns(4)

n_sessions = len(filtered_df)
n_athletes = filtered_df["athlete_number"].nunique() if n_sessions else 0
avg_load   = filtered_df["session_load"].mean() if n_sessions else 0
avg_dist   = filtered_df["total_distance_m"].mean() if n_sessions else 0

_kpi(col_h1, "Sessions",          f"{n_sessions:,}", delta="cohort total", delta_dir="flat")
_kpi(col_h2, "Unique Athletes",   f"{n_athletes:,}")
_kpi(col_h3, "Avg Session Load",  f"{avg_load:,.1f}", delta="±SD across cohort", delta_dir="flat")
_kpi(col_h4, "Avg Total Dist",    f"{avg_dist:,.0f}", unit="m")

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_age, tab_athlete, tab_benchmark, tab_chat = st.tabs(
    ["Overview", "Age Group (DS Metrics)", "Athlete Drilldown", "Benchmarks", "Chat"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 - Overview
# ══════════════════════════════════════════════════════════════════════════════

with tab_overview:

    if filtered_df.empty:
        st.warning("No data matches the current filters.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            with chart_card("Session Load Distribution", "Box + outliers, by sport"):
                st.plotly_chart(
                    viz.plot_session_load_distribution(filtered_df, group_by="athlete_sport", title=""),
                    use_container_width=True,
                )

        with c2:
            with chart_card("Volume vs Intensity", "active_minutes × session_load · size = distance"):
                st.plotly_chart(
                    viz.plot_volume_vs_intensity(filtered_df, color_by="athlete_sport"),
                    use_container_width=True,
                )

        c3, c4 = st.columns(2)

        with c3:
            with chart_card("Distance Breakdown", "Mean total / high-intensity / sprint distance per sport"):
                st.plotly_chart(
                    viz.plot_distance_breakdown(filtered_df, group_col="athlete_sport", title=""),
                    use_container_width=True,
                )

        with c4:
            with chart_card("Speed Profile", "Average vs max speed"):
                st.plotly_chart(
                    viz.plot_speed_profile(filtered_df, color_by="athlete_gender_marker"),
                    use_container_width=True,
                )

        with chart_card("Accel / Decel Load", "Event counts by sport"):
            st.plotly_chart(
                viz.plot_accel_decel_heatmap(filtered_df, group_col="athlete_sport", title=""),
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 - Age Group (DS Metrics)
# ══════════════════════════════════════════════════════════════════════════════

with tab_age:

    st.markdown(
        "**Source:** DS team pipeline (r_pipeline.txt) - "
        "sessions filtered to `active_minutes ≥ {}`, then grouped by age.".format(min_minutes)
    )

    if summary_df.empty:
        st.warning("Not enough data for age-group analysis with current filters.")
    else:
        metric_choice = st.selectbox(
            "Metric",
            options=PERF_METRICS,
            format_func=lambda m: m.replace("_", " ").title(),
            key="age_metric",
        )

        with chart_card(
            f"{metric_choice.replace('_',' ').title()} by Age Group",
            "Mean ±1 SD with 10/90 percentile markers",
        ):
            st.plotly_chart(
                viz.plot_age_group_summary(summary_df, metric=metric_choice),
                use_container_width=True,
            )

        with chart_card(
            "Athlete Scatter",
            "Individual athletes, coloured by gender",
        ):
            st.plotly_chart(
                viz.plot_age_metric_scatter(
                    athlete_df if not athlete_df.empty else filtered_df,
                    metric=metric_choice,
                    color_by="athlete_gender_marker",
                ),
                use_container_width=True,
            )

        with chart_card("Age-Group Summary Table", "DS averages"):
            st.dataframe(
                summary_df.style.format(precision=2),
                use_container_width=True,
                height=300,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 - Athlete Drilldown
# ══════════════════════════════════════════════════════════════════════════════

with tab_athlete:

    if filtered_df.empty:
        st.warning("No data matches the current filters.")
    else:
        athlete_ids = sorted(filtered_df["athlete_number"].dropna().unique().tolist())
        sel_athlete = st.selectbox(
            "Select Athlete",
            options=athlete_ids,
            format_func=lambda x: f"Athlete #{int(x)}",
        )

        athlete_sessions = filtered_df[filtered_df["athlete_number"] == sel_athlete]

        if athlete_sessions.empty:
            st.warning("No sessions found for this athlete with current filters.")
        else:
            age = int(athlete_sessions["athlete_relative_age"].iloc[0])
            sport = athlete_sessions["athlete_sport"].iloc[0].replace("_", " ").title()
            gender = athlete_sessions["athlete_gender_marker"].iloc[0].title()
            n_sess = len(athlete_sessions)

            info_cols = st.columns(4)
            _kpi(info_cols[0], "Age",      str(age))
            _kpi(info_cols[1], "Sport",    sport)
            _kpi(info_cols[2], "Gender",   gender)
            _kpi(info_cols[3], "Sessions", str(n_sess))

            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

            c_left, c_right = st.columns([2, 1])

            with c_left:
                with chart_card("Session Timeline", "Per-session distance, load and max speed"):
                    st.plotly_chart(
                        viz.plot_athlete_sessions(filtered_df, athlete_id=sel_athlete),
                        use_container_width=True,
                    )

            with c_right:
                with chart_card("Percentile Ranks", "vs age-group peers"):
                    ranked_rows = athlete_df[athlete_df["athlete_number"] == sel_athlete]
                    if not ranked_rows.empty:
                        latest_row = ranked_rows.iloc[-1]
                        st.plotly_chart(
                            viz.plot_percentile_radar(latest_row),
                            use_container_width=True,
                        )
                    else:
                        st.info("Percentile ranks not available (need ≥ 2 athletes in age group).")

            with chart_card("Session Detail", "All sessions for this athlete under current filters"):
                display_cols = [
                    "active_minutes", "total_distance_m", "max_speed_kph",
                    "session_load", "high_intensity_events", "sprint_events",
                    "acceleration_events", "deceleration_events",
                ]
                avail_cols = [c for c in display_cols if c in athlete_sessions.columns]
                st.dataframe(
                    athlete_sessions[avail_cols].reset_index(drop=True).style.format(precision=2),
                    use_container_width=True,
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 - Benchmarks
# ══════════════════════════════════════════════════════════════════════════════

with tab_benchmark:

    if filtered_df.empty:
        st.warning("No data matches the current filters.")
    else:
        with chart_card(
            "Sport Benchmark Heatmap",
            "Mean performance metrics · values raw, color normalized",
        ):
            st.plotly_chart(
                viz.plot_sport_benchmark_heatmap(filtered_df),
                use_container_width=True,
            )

        bench_col = st.selectbox(
            "Breakdown by",
            options=["athlete_sport", "club_division", "athlete_gender_marker"],
            format_func=lambda c: c.replace("_", " ").title(),
            key="bench_col",
        )

        c_b1, c_b2 = st.columns(2)
        bench_label = bench_col.replace("_", " ").title()

        with c_b1:
            with chart_card(f"Session Load by {bench_label}", "Box + outliers"):
                st.plotly_chart(
                    viz.plot_session_load_distribution(filtered_df, group_by=bench_col, title=""),
                    use_container_width=True,
                )

        with c_b2:
            with chart_card(f"Distance Breakdown by {bench_label}", "Mean total / HI / sprint"):
                st.plotly_chart(
                    viz.plot_distance_breakdown(filtered_df, group_col=bench_col, title=""),
                    use_container_width=True,
                )

        with chart_card(f"Accel / Decel by {bench_label}", "Event counts"):
            st.plotly_chart(
                viz.plot_accel_decel_heatmap(filtered_df, group_col=bench_col, title=""),
                use_container_width=True,
            )

        with chart_card("Raw Data (filtered)", f"{len(filtered_df):,} rows"):
            st.dataframe(
                filtered_df.reset_index(drop=True),
                use_container_width=True,
                height=350,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 - Chat
# ══════════════════════════════════════════════════════════════════════════════

with tab_chat:

    # Athlete selector (independent of the drilldown tab)
    chat_col, _ = st.columns([1, 2])
    with chat_col:
        chat_athlete_ids = sorted(raw_df["athlete_number"].dropna().unique().tolist())
        chat_sel_id = st.selectbox(
            "Athlete context",
            options=[None] + chat_athlete_ids,
            format_func=lambda x: "No athlete selected" if x is None else f"Athlete #{int(x)}",
            key="chat_athlete_sel",
        )

    if chat_sel_id is not None:
        row = raw_df[raw_df["athlete_number"] == chat_sel_id].iloc[0]
        st.caption(
            f"Sport: {row['athlete_sport'].replace('_', ' ').title()} | "
            f"Division: {row['club_division'].upper()} | "
            f"Gender: {row['athlete_gender_marker'].title()} | "
            f"Age: {int(row['athlete_relative_age'])}"
        )

    st.divider()

    # Session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Welcome message on first load
    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown(_HELP_TEXT)

    # Render conversation history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Clear button
    if st.button("Clear conversation", key="chat_clear"):
        st.session_state.chat_history = []
        st.rerun()

    # Chat input
    if user_input := st.chat_input("Ask about performance data...", key="chat_input"):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        response = _dispatch(
            user_input,
            int(chat_sel_id) if chat_sel_id is not None else None,
        )

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
