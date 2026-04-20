import fastf1 as ff1
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

ff1.Cache.enable_cache("f1_cache")


class F1DataPipeline:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="f1_strategy",
            user="f1_analyst",
            password="f1_strategy_2025",
        )
        self.cursor = self.conn.cursor()

    def ensure_season_exists(self, year):
        self.cursor.execute("SELECT season_id FROM seasons WHERE year = %s", (year,))
        result = self.cursor.fetchone()

        if not result:
            self.cursor.execute(
                "INSERT INTO seasons (season_id, year) VALUES (%s, %s)", (year, year)
            )
            self.conn.commit()
            return year
        return result[0]

    def ensure_team_exists(self, team_name):
        if not team_name:
            return None
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
        print(f"🏁 Ingesting {year} {grand_prix}...")

        # Clear any stuck transaction before starting
        self.conn.rollback()

        # Get season ID
        season_id = self.ensure_season_exists(year)

        # Load race session
        race = ff1.get_session(year, grand_prix, "R")
        race.load()

        # Insert race
        self.cursor.execute(
            """
            INSERT INTO races (season_id, round_number, race_name, circuit_name, race_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (season_id, round_number) DO UPDATE
            SET race_name = EXCLUDED.race_name
            RETURNING race_id
        """,
            (
                season_id,
                int(race.event["RoundNumber"]),
                race.event["EventName"],
                race.event["Location"],
                race.date,
            ),
        )

        race_id = self.cursor.fetchone()[0]
        self.conn.commit()
        print(f"   Race ID: {race_id}")

        # Process drivers and results
        for driver_code in race.drivers:
            driver_info = race.get_driver(driver_code)
            team_id = self.ensure_team_exists(driver_info.get("TeamName", "Unknown"))

            # Insert or update driver
            self.cursor.execute(
                """
                INSERT INTO drivers (driver_id, driver_name, team_id, driver_number)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (driver_id) DO UPDATE
                SET team_id = EXCLUDED.team_id
            """,
                (
                    driver_code,
                    driver_info["FullName"],
                    team_id,
                    (
                        int(driver_info.get("DriverNumber", 0))
                        if driver_info.get("DriverNumber")
                        else 0
                    ),
                ),
            )
            
            def get_all_races()

            # Get race result
            result = race.results[race.results["Abbreviation"] == driver_code]
            if not result.empty:
                self.cursor.execute(
                    """
                    INSERT INTO race_results (race_id, driver_id, final_position, points, status)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (race_id, driver_id) DO UPDATE
                    SET final_position = EXCLUDED.final_position
                """,
                    (
                        race_id,
                        driver_code,
                        int(result["Position"].iloc[0]),
                        float(result["Points"].iloc[0]),
                        result["Status"].iloc[0][:50],
                    ),
                )

        self.conn.commit()
        print(f"   Processed {len(race.drivers)} drivers")

        # Process lap times - THE PROBLEM AREA
        laps = race.laps
        lap_data = []

        for _, lap in laps.iterrows():
            # Convert lap time to seconds (float)
            lap_time = None
            if lap["LapTime"]:
                lap_time = float(lap["LapTime"].total_seconds())

            # Convert sector times to seconds
            sector1 = None
            if lap["Sector1Time"]:
                sector1 = float(lap["Sector1Time"].total_seconds())

            sector2 = None
            if lap["Sector2Time"]:
                sector2 = float(lap["Sector2Time"].total_seconds())

            sector3 = None
            if lap["Sector3Time"]:
                sector3 = float(lap["Sector3Time"].total_seconds())

            # Get tire compound (ensure it's a string, not numpy type)
            compound = lap.get("Compound", None)
            if compound is not None and not pd.isna(compound):
                compound = str(compound)

            lap_data.append(
                (
                    race_id,
                    lap["Driver"],
                    int(lap["LapNumber"]),
                    lap_time,
                    sector1,
                    sector2,
                    sector3,
                    (
                        int(lap["Position"])
                        if lap["Position"] and not pd.isna(lap["Position"])
                        else None
                    ),
                    compound,
                    (
                        int(lap.get("TyreLife", None))
                        if lap.get("TyreLife") and not pd.isna(lap.get("TyreLife"))
                        else None
                    ),
                )
            )

        # Insert in smaller batches
        batch_size = 500
        for i in range(0, len(lap_data), batch_size):
            batch = lap_data[i : i + batch_size]
            try:
                execute_values(
                    self.cursor,
                    """
                    INSERT INTO lap_times (race_id, driver_id, lap_number, lap_time, 
                                         sector1_time, sector2_time, sector3_time, position,
                                         tire_compound, tire_life)
                    VALUES %s
                    ON CONFLICT (lap_id) DO NOTHING
                """,
                    batch,
                )
                self.conn.commit()
                print(f"   Inserted laps {i} to {i+len(batch)}")
            except Exception as e:
                print(f"   Error on batch {i}: {e}")
                self.conn.rollback()
                # Try one by one to find bad record
                for single in batch:
                    try:
                        execute_values(
                            self.cursor,
                            """
                            INSERT INTO lap_times (race_id, driver_id, lap_number, lap_time, 
                                                 sector1_time, sector2_time, sector3_time, position,
                                                 tire_compound, tire_life)
                            VALUES %s
                        """,
                            [single],
                        )
                        self.conn.commit()
                    except Exception as single_err:
                        print(f"     Skipping bad record: {single[2]} - {single_err}")
                        self.conn.rollback()

        print(f"   Processed {len(lap_data)} laps")

        # Process stints (similar batch approach)
        stints_data = []
        for driver in race.drivers:
            driver_laps = race.laps.pick_driver(driver)
            if driver_laps.empty:
                continue

            stint_num = 1
            current_stint = []
            current_compound = None

            for _, lap in driver_laps.iterrows():
                compound = lap.get("Compound", None)
                if compound is not None and not pd.isna(compound):
                    compound = str(compound)

                if compound != current_compound and current_stint:
                    lap_times = []
                    for l in current_stint:
                        if l["LapTime"]:
                            lap_times.append(float(l["LapTime"].total_seconds()))

                    avg_time = sum(lap_times) / len(lap_times) if lap_times else None

                    stints_data.append(
                        (
                            race_id,
                            driver,
                            stint_num,
                            int(current_stint[0]["LapNumber"]),
                            int(current_stint[-1]["LapNumber"]),
                            current_compound,
                            len(current_stint),
                            avg_time,
                        )
                    )
                    stint_num += 1
                    current_stint = []

                current_stint.append(lap)
                current_compound = compound

            # Last stint
            if current_stint:
                lap_times = []
                for l in current_stint:
                    if l["LapTime"]:
                        lap_times.append(float(l["LapTime"].total_seconds()))

                avg_time = sum(lap_times) / len(lap_times) if lap_times else None

                stints_data.append(
                    (
                        race_id,
                        driver,
                        stint_num,
                        int(current_stint[0]["LapNumber"]),
                        int(current_stint[-1]["LapNumber"]),
                        current_compound,
                        len(current_stint),
                        avg_time,
                    )
                )

        if stints_data:
            for i in range(0, len(stints_data), batch_size):
                batch = stints_data[i : i + batch_size]
                try:
                    execute_values(
                        self.cursor,
                        """
                        INSERT INTO stints (race_id, driver_id, stint_number, start_lap, end_lap,
                                           tire_compound, stint_length, avg_lap_time)
                        VALUES %s
                    """,
                        batch,
                    )
                    self.conn.commit()
                except Exception as e:
                    print(f"   Stint batch error: {e}")
                    self.conn.rollback()

        print(f"   Processed {len(stints_data)} stints")
        print(f"✅ Completed {year} {grand_prix}")

    def close(self):
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    pipeline = F1DataPipeline()
    pipeline.ingest_race(2023, "Monaco")
    pipeline.close()
