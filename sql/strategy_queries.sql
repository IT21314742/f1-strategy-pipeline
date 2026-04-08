SELECT 
    r.race_name,
    d.driver_name,
    s.tire_compound,
    COUNT(*) as stint_count,
    AVG(s.stint_length) as avg_stint_length
FROM stints s
JOIN races r ON s.race_id = r.race_id
JOIN drivers d ON s.driver_id = d.driver_id
WHERE r.season_id = 2023
GROUP BY r.race_name, d.driver_name, s.tire_compound
ORDER BY avg_stint_length ASC
LIMIT 10;

--2. Undercut effectiveness: Driver who gained positions after pit stops
WITH pit_stop_analysis AS (
    SELECT
        driver_id,
        race_id,
        lap_number,
        position,
        LAG(position) OVER (PARTITION BY driver_id, race_id ORDER BY lap_number) AS prev_position
        FROM lap_times
        WHERE lap_times IS NOT NULL
)
SELECT 
r.race_name
d.driver_name
COUNT(*) AS pit_stops_analyzed,
AVG(prev_position -  position) AS avg_positions_gained
FROM pit_stop_analysis p
JOIN races r ON p.race_id = r.race_id
JOIN drivers d ON p.driver_id = d.driver_id
WHERE prev_position > position -- gained Positions
GROUP BY r.race_name, d.driver_name
HAVING COUNT(*) > 1