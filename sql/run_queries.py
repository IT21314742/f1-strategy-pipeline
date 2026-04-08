import psycopg2
import pandas as pd


conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="f1_strategy",
    user="f1_analyst",
    password="f1_strategy_2025"
)


# Run each query and export to csv
queries = {
    "tire_strategies": """
    r.race_name,
    d.driver_name,
    s.tire_compound,
    AVG(s.stint_length) as avg_stint_length
FROM stints s
JOIN races r ON s.race_id = r.race_id
JOIN drivers d ON s.driver_id = d.driver_id
    """
}