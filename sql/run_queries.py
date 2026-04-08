import psycopg2
import pandas as pd


conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="f1_strategy",
    
)