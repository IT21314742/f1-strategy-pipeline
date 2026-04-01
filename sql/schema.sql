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
    date_of_birth DATE,
    team_id VARCHAR(10) REFERENCES teams(team_id),
    driver_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Races dimension
CREATE TABLE races (
    race_id SERIAL PRIMARY KEY,
    season_id INT REFERENCES seasons(season_id),
    round_number INT NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    circuit_name VARCHAR(100),
    country VARCHAR(50),
    race_date DATE,
    qualifying_date DATE,
    UNIQUE(season_id, round_number)
);

-- Qualifying results fact table
CREATE TABLE qualifying_results (
    qualifying_id SERIAL PRIMARY KEY,
    race_id INT REFERENCES races(race_id),
    driver_id VARCHAR(3) REFERENCES drivers(driver_id),
    q1_time TIME,
    q2_time TIME,
    q3_time TIME,
    grid_position INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Race results fact table
CREATE TABLE race_results (
    result_id SERIAL PRIMARY KEY,
    race_id INT REFERENCES races(race_id),
    driver_id VARCHAR(3) REFERENCES drivers(driver_id),
    final_position INT,
    points DECIMAL(5,2),
    status VARCHAR(50),
    fastest_lap_time TIME,
    fastest_lap_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lap times fact table (IMPORTANT)
CREATE TABLE lap_times (
    lap_id BIGSERIAL PRIMARY KEY,
    race_id INT REFERENCES races(race_id),
    driver_id VARCHAR(3) REFERENCES drivers(driver_id),
    lap_number INT NOT NULL,
    sector1_time TIME
    sector2_time TIME
    sector_time TIME
)