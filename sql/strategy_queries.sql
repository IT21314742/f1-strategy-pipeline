-- 1. Tire strategies (Shortest Stints)
SELECT
r.race_name,
d.drover_name,
s.tire_compound,
COUNT(*) as stint_count,
AVG(s.stint_length) as avg_stint_length