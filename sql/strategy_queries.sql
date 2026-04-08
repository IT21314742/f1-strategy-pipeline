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
        LAG(position) OVER (PARTITION BY driver_id, race_id ORDER BY lap_number) as prev_position
    FROM lap_times
    WHERE lap_time IS NOT NULL
)
SELECT 
    r.race_name,
    d.driver_name,
    COUNT(*) as pit_stops_analyzed,
    AVG(prev_position - position) as avg_positions_gained
FROM pit_stop_analysis p
JOIN races r ON p.race_id = r.race_id
JOIN drivers d ON p.driver_id = d.driver_id
WHERE prev_position > position  -- Gained positions
GROUP BY r.race_name, d.driver_name
HAVING COUNT(*) > 1
ORDER BY avg_positions_gained DESC
LIMIT 20;


---3. Qualifying vs Race performance
SELECT
    d.driver_name,
    t.team_name,
    AVG(q.grid_position) as avg_qualifying,
    AVG(r.final_position) as avg_race_finish,
    AVG(q.grid_position - r.final_position) as avg_positions_gained
FROM qualifying_results q
JOIN rese_results r ON q.race_id = r.race_id AND q.driver_id = r.race_id
JOIN drivers d ON q.driver_id = d.driver_id
JOIN teams t ON d.team_id = t.team_id
GROUP BY d.driver_name, t.team_name
HAVING COUNT(*) >=5
ORDER BY avg_positions_gained DESC;