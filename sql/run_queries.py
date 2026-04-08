import psycopg2
import pandas as pd


conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="f1_strategy",
    user="f1_analyst",
    password="f1_strategy_2025"
)


