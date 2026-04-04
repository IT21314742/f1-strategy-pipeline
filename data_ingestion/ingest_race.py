import fastapi as ff1
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os

# Enable cache
ff1.Cache.enable_cache("f1_cache")


class F1DataPipeline:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="f1_analyst",
            user="f1_analyst",
            password="f1_strategy_2025",
        )
        self.cursor = self.conn.cursor()

    def ensure_season_exists(self, year):
        """
        Check if season exists in database, insert if not
        """
        self.cursor.execute(
            "SELECT season_id FROM seasons WHERE year = %s"(
                year,
            )
        )
        result = self.cursor.fetchone()

        if not result:
            self.cursor.execute(
                "INSERT INTO seasons (season_id, year) VALUES (%s, %s)",
            )
            self.conn.commit()
            return year
        return result[0]

    def ensure_team_exists(self, team_name):
        """Insert team if not exists"""
        team_id = team_name.replace(" ", "_").upper()[:10]

        self.cursor.execute("SELECT team_id FROM teams WHERE team_id = %s", (team_id,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO teams (team_id, team_name) VALUES (%s, %s)",
                (team_id, team_name),
            )
            self.conn.commit()
        return team_id

    def ingest_race(self, year, grand_prix):
        """Ingest all data for a race"""
        print(f"🏁 Ingesting {year} {grand_prix}...")

        # Get season ID
        season_id = self.ensure_season_exists(year)

        # Load race session
        race = ff1.get_session(year, grand_prix, "R")
        race.load()

        # Insert race
        self.cursor.execute(
            """
                            INSERT INTO races (season_id, round_number, race_name, circuit_name, race_date)
                            
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (season_id, round_number) DO NOTHING
                            RETURNING race_id
                            """,
            (
                season_id,
                race.event["RoundNumber"],
                race.event["EventName"],
                race.event["Location"],
                race.date,
            ),
        )

        race_id_result = self.cursor.fetchone()
        if race_id_result:
            race_id = race_id_result[0]
        else:
            # Race exists, get its ID
            self.cursor.execute(
                "SELECT race_id, FROM races WHERE season_id = %s AND round_number = %s",
                (season_id, race.event["RoundNumber"]),
            )
            race_id = self.cursor.fetchone()[0]

        # Process drivers and results
        for driver_code in race.drivers:
            driver_info = race.get_driver(driver_code)

            # Ensure team exists
            team_id = self.ensure_team_exists(driver_info["TeamName"])

            # Insert Driver
            self.cursor.execute(
                """
                                INSERT INTO drivers (driver_id, driver_name, team_id, driver_number)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (driver_id) DO UPDATE
                                SET team_id = EXCLUDED.team_id
                                """,
                (
                    driver_code,
                    driver_info["Fullname"],
                    team_id,
                    driver_info.get("DriverNumber", 0),
                ),
            )

            # Get Race Results
            result = race.results[race.results["Abbreviation"] == driver_code]
            if not result.empty:
                self.cursor.execute(
                    """
                                    INSERT INTO race_results (race_id, driver_id, final_position, points, status)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT DO NOTHING""",
                    (
                        race_id,
                        driver_code,
                        int(result["Position"].iloc[0]),
                        float(result["Points"].iloc[0]),
                        result["Status"].iloc[0],
                    ),
                )

        # Process Lap Times
        laps = race.laps
        lap_data = []
        for _, lap in laps.iterrows():
            lap_data.append(
                (
                    race_id,
                    lap["Driver"],
                    lap["LapNumber"],
                    lap["LapTime"].total_seconds() if lap["LapTime"] else None,
                    lap["Sector1Time"].total_seconds() if lap["Sector1Time"] else None,
                    lap["Sector2Time"].total_seconds() if lap["Sector2Time"] else None,
                    lap["Sector3Time"].total_seconds() if lap["Sector3Time"] else None,
                    lap["Position"],
                    lap.get("Compound", None),
                    lap.get("TyreLife", None),
                )
            )

        if lap_data:
            execute_values(
                self.cursor,
                """
                           INSERT INTO lap_times (race_id, driver_id, lap_number, lap_time, sector1_time, sector2_time, sector3_time, position, tire_compound, tire_life)
                           VALUES %s
                           """,
                lap_data,
            )
        
        # Process Stints
        stints_data = []
        for driver in race.drivers:
            driver_laps = race.laps.pick_driver(driver)
            if driver_laps.empty:
                continue
            
            stints_num = 1
            current_stint = []
            current_compound = None
            
            for _, lap in driver_laps.iterrows():
                compound = lap.get('compound')
                if compound != current_compound and current_stint:
                    # Stint ended
                    stints_data.append((
                        race_id, driver, stints_num,
                        current_stint[0]['LapNumber'],
                        current_stint[-1]['LapNumber'],
                        current_compound,
                        len(current_stint),
                        sum(1['LapTime'].total_seconds() for 1 in current_stint if 1['LapTime']) / len(current_stint)
                        
                    ))
                    stints_num += 1
                    current_stint = []
                
                current_stint.append(lap)
                current_compound = compound
            
            # Last stint
            if current_stint:
                stints_data.append((
                    race_id, driver, stints_num,
                    
                ))
