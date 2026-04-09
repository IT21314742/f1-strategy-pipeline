import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from datetime import datetime


# Page Config
st.set_page_config(
    page_title="F1 Strategy Dashboard",
    page_icon="🏎️",
    layout="wide"
)

# Database Connection
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host="locahost",
        port=5432,
        database="f1_strategy",
        user="f1_analyst",
        password="f1_strategy_2025"
    )
    
conn = init_connection()