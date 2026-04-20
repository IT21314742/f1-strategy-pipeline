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

    def get_all_races(self, year):
        """Get all Grand Prix names for a given season"""
        schedule = ff1.get_event_schedule(year)
        # Filter out testing events, keep only Grands Prix
        races = schedule[schedule['EventFormat'] == 'conventional']['EventName'].tolist()
        return races

    def update_driver_details(self):
        """Update driver nationalities and birth dates"""
        
        # Complete 2023 driver data
        driver_info = {
            'VER': {'nationality': 'Netherlands', 'date_of_birth': '1997-09-30', 'driver_name': 'Max Verstappen'},
            'PER': {'nationality': 'Mexico', 'date_of_birth': '1990-01-26', 'driver_name': 'Sergio Perez'},
            'HAM': {'nationality': 'United Kingdom', 'date_of_birth': '1985-01-07', 'driver_name': 'Lewis Hamilton'},
            'RUS': {'nationality': 'United Kingdom', 'date_of_birth': '1998-02-15', 'driver_name': 'George Russell'},
            'LEC': {'nationality': 'Monaco', 'date_of_birth': '1997-10-16', 'driver_name': 'Charles Leclerc'},
            'SAI': {'nationality': 'Spain', 'date_of_birth': '1994-09-01', 'driver_name': 'Carlos Sainz'},
            'NOR': {'nationality': 'United Kingdom', 'date_of_birth': '1999-11-13', 'driver_name': 'Lando Norris'},
            'PIA': {'nationality': 'Australia', 'date_of_birth': '2001-04-02', 'driver_name': 'Oscar Piastri'},
            'ALO': {'nationality': 'Spain', 'date_of_birth': '1981-07-29', 'driver_name': 'Fernando Alonso'},
            'STR': {'nationality': 'Canada', 'date_of_birth': '1998-10-29', 'driver_name': 'Lance Stroll'},
            'GAS': {'nationality': 'France', 'date_of_birth': '1996-02-07', 'driver_name': 'Pierre Gasly'},
            'OCO': {'nationality': 'France', 'date_of_birth': '1996-09-17', 'driver_name': 'Esteban Ocon'},
            'TSU': {'nationality': 'Japan', 'date_of_birth': '2000-05-11', 'driver_name': 'Yuki Tsunoda'},
            'RIC': {'nationality': 'Australia', 'date_of_birth': '1989-07-01', 'driver_name': 'Daniel Ricciardo'},
            'HUL': {'nationality': 'Germany', 'date_of_birth': '1987-08-19', 'driver_name': 'Nico Hulkenberg'},
            'MAG': {'nationality': 'Denmark', 'date_of_birth': '1992-10-05', 'driver_name': 'Kevin Magnussen'},
            'BOT': {'nationality': 'Finland', 'date_of_birth': '1989-08-28', 'driver_name': 'Valtteri Bottas'},
            'ZHO': {'nationality': 'China', 'date_of_birth': '1999-05-30', 'driver_name': 'Zhou Guanyu'},
            'ALB': {'nationality': 'Thailand', 'date_of_birth': '1996-03-23', 'driver_name': 'Alexander Albon'},
            'SAR': {'nationality': 'United States', 'date_of_birth': '2000-10-27', 'driver_name': 'Logan Sargeant'},
        }
        
        updated_count = 0
        for driver_id, info in driver_info.items():
            self.cursor.execute("""
                UPDATE drivers 
                SET nationality = %s, date_of_birth = %s, driver_name = %s
                WHERE driver_id = %s
            """, (info['nationality'], info['date_of_birth'], info['driver_name'], driver_id))
            updated_count += 1
        
        self.conn.commit()
        print(f"✅ Updated {updated_count} drivers with nationality and DOB")

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

        # Process lap times
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

        # Process stints
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
    
    # Update driver details first (adds nationality and DOB)
    pipeline.update_driver_details()
    
    # Get all 2023 races automatically
    all_races = pipeline.get_all_races(2023)
    print(f"\n🏁 Found {len(all_races)} races for 2023 season:")
    for i, race in enumerate(all_races, 1):
        print(f"   {i}. {race}")
    
    # Ingest each race
    print("\n" + "="*50)
    for race in all_races:
        try:
            pipeline.ingest_race(2023, race)
        except Exception as e:
            print(f"❌ Failed {race}: {e}")
            continue
    
    pipeline.close()
    print("\n" + "="*50)
    print("🎉 Complete 2023 season ingested successfully!")
    print(f"   Total races: {len(all_races)}")
    print("   Run your dashboard: streamlit run dashboard/strategy_dashboard.py")
            