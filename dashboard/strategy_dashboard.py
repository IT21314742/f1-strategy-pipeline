import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from datetime import datetime


# Page Config
st.set_page_config(page_title="F1 Strategy Dashboard", page_icon="🏎️", layout="wide")


# Database Connection
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host="locahost",
        port=5432,
        database="f1_strategy",
        user="f1_analyst",
        password="f1_strategy_2025",
    )


conn = init_connection()


@st.cache_data(ttl=3600)
def load_races():
    return pd.read_sql(
        """
        SELECT race_id, race_name, circuit_name, race_date
        FROM races
        ORDER BY race_date DESC
        """,
        conn,
    )


@st.cache_data(ttl=3600)
def load_stints(race_id):
    return pd.read_sql(
        f"""
        SELECT
            d.driver_name,
            s.stint_number,
            s.tire_compound,
            s.start_lap,
            s.end_lap,
            s.stint_length,
            s.avg_lap_time
        FROM stints s
        JOIN drivers d ON s.driver_id = d.driver_id
        WHERE s.race_id = {race_id}
        ORDER BY s.start_lap
        """,
        conn,
    )


@st.cache_data(ttl=3600)
def load_lap_times(race_id):
    return pd.read.sql(
        f"""
        SELECT
            d.driver_name,
            l.lap_number,
            l.lap_time,
            l.position,
            l.tire_compound,
            l.tire_life
        FROM lap_times l
        JOIN drivers d ON 1.driver_id = d.driver_id
        WHERE 1.race_id = {race_id}
        ORDER BY 1.lap_number
        """,
        conn,
    )


# Title
st.title("🏎️ F1 Strategy Analysis Dashboard")
st.markdown(
    """
        Analyze tire strategies, pit windows, and driver performance across races.
        Built with **FastF1**, **PostgreSQL***, and **Streamlit**.
        """
)

# Sidebar
with st.sidebar:
    st.header("📊 Filters")

    # Race selector
    races_df = load_races()
    selected_race = st.selectbox(
        "Select Race",
        races_df["race_id"].tolist(),
        format_func=lambda x: races_df[races_df["race_id"] == x]["race_name"].iloc[0],
    )

    # Driver selector
    drivers_df = load_drivers()
    selected_drivers = st.multiselect(
        "Select Drivers (Optional)",
        drivers_df["driver_id"].tolist(),
        format_func=lambda x: drivers_df[drivers_df["driver_id"] == x][
            "driver_name"
        ].iloc[0],
    )

    st.markdown("---")
    st.caption(f"Data Source: FastF1 API")
    st.caption(f"last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Load Data
stints_df = load_stints(selected_race)
laps_df = load_lap_times(selected_race)

if selected_drivers:
    stints_df = stints_df[stints_df["driver_name"].isin(selected_drivers)]
    laps_df = laps_df[laps_df["driver_name"].isin(selected_drivers)]


# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏎 Tire Stint Analysis")

    # Create stint chart
    fig_stints = go.Figure()

    for driver in stints_df["driver_name"].unique():
        driver_stints = stints_df[stints_df["driver_name"] == driver]

        for _, stint in driver_stints.iterrows():
            color = {
                "SOFT": "red",
                "MEDIUM": "yellow",
                "HARD": "gray",
                "INTERMEDIATE": "green",
                "WET": "blue",
            }.get(stint["tire_compound"], "gray")

            fig_stints.add_trace(
                go.Bar(
                    name=f"{driver} - {stint['tire_compound']}",
                    x=[driver],
                    y=[stint["stint_length"]],
                    base=[stint["start_lap"]],
                    marker_color=color,
                    text=f"{stint['tire_compound']}<br>Laps: {stint['start_lap']}-{stint['end_lap']}",
                    hoverinfo="text",
                    showlegend=False,
                )
            )

    fig_stints.update_layout(
        title="Tire Stints Strategy by Driver",
        xaxis_title="Driver",
        yaxis_title="Lap Number",
        barmode="stack",
        height=500,
    )

    st.plotly_chart(fig_stints, use_container_width=True)

with col2:
    st.subheader("📈 Lap Time Comparison")
    
    #Lap time comparison
    fig_laps = px.line(
        laps_df,
        x='lap_number',
        y='lap_time',
        color='driver_name',
        title="Lap Time Throughout the Race"
    )
    
    fig_laps.update_layout(
        yaxis_title="Lap Time (seconds)",
        xaxis_title="Lap Number",
        height=500
    )
    
    st.plotly_chart(fig_laps, use_container_width=True)
    
# Third row: Performance Metrics
st.subheader("📊 Key Performance Metrics")

col3, col4, col5 = st.columns(3)

with col3:
    #Best Stint
    