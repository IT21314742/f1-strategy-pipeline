-- 1. Tire strategies (Shortest Stints)
SELECT
r.race_name,
d.drover_name,
s.tire_compound,
COUNT(*) as stint_count,
AVG(s.stint_length) as avg_stint_length
FROM stints s
JOIN races r ON s.race_id = r.race_id
JOIN drivers d ON s.driver_id = d.driver_id
WHERE r.season_id = 2025
GROUP BY r.race_name, 