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

#Sidebar
with st.sidebar:
    st.header("📊 Filters")
    
    # Race selector
    races_df = load_races()
    selected_race = st.selectbox(