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
WHERE r.season_id = 2023
GROUP BY r.race_name, d.driver_name, s.tire_compound
ORDER BY avg_stint_length ASC
LIMIT 20
    """,
"Undercut_masters":"""
WITH pit_stop_analysis AS (
    SELECT
    driver_id,
    race_id,
    lap_number,
    position,
    LAG(position) OVER (PARTITION BY driver_id, race_id ORDER BY lap_number) as prev_position FROM lap_times
    )
    SELECT
    d.driver_name,
    AVG(prev_position - position) as avg_position_gained
    FROM pit_stop_analysis p
    JOIN drivers d ON p.driver_id = d.driver_id
    WHERE prev_position > position
    GROUP BY d.driver_name
    HAVING COUNT(*) > 5
    ORDER BY avg_position_gained DESC"""

}
