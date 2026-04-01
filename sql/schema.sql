-- were following a clean state protocol here. so in order to do that, first we need to clear anything in the database similar to what were gonna add later.
-- So were going to Drop tables if they exist

DROP TABLE IF EXISTS lap_times CASCADE;
DROP TABLE IF EXISTS stints CASCADE;
DROP TABLE IF EXISTS race_results CASCADE;
DROP TABLE IF EXISTS qualifying_results CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS races CASCADE;
DROP TABLE IF EXISTS seasons CASCADE;


--- Seasons dimension
CREATE TABLE seasons (
    season_id INT PRIMARY KEY,
    year INT NOT NULL UNIQUE,
    champion_driver_id VARCHAR(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams dimension
CREATE TABLE teams (
    team_id VARCHAR(10) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    engine_manufacturer VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drivers dimension
CREATE TABLE drivers (
    driver_id VARCHAR(3) PRIMARY KEY,
    driver_name VARCHAR(100) NOT NULL,
    nationality VARCHAR(50),
    date_of_birth DATE;
    team_id VARCHAR(10) REFERENCES teams(team_id),
    driver_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

