import fastf1 as ff1
import psycopg2
import numpy as np

ff1.Cache.enable_cache('f1_cache')

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="f1_strategy",
    user="f1_analyst",
    password="f1_strategy_2025"
)
cursor = conn.cursor()

# Clear any stuck transaction
conn.rollback()

def clean_value(val):
    """Clean values for database insertion"""
    if val is None:
        return None
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    if isinstance(val, float):
        return val
    return val

print("🏁 Loading Monaco 2023...")

# Load race
race = ff1.get_session(2023, 'Monaco', 'R')
race.load()

print(f"✅ Loaded {len(race.drivers)} drivers")

# Insert season
cursor.execute("DELETE FROM seasons WHERE year = 2023")
cursor.execute("INSERT INTO seasons (season_id, year) VALUES (2023, 2023)")

# Insert race
race_date = race.date if race.date else None
cursor.execute("""
    DELETE FROM races WHERE season_id = 2023 AND round_number = %s
""", (clean_value(race.event['RoundNumber']),))

cursor.execute("""
    INSERT INTO races (season_id, round_number, race_name, circuit_name, race_date)
    VALUES (2023, %s, %s, %s, %s)
    RETURNING race_id
""", (
    clean_value(race.event['RoundNumber']),
    str(race.event['EventName'])[:100],
    str(race.event['Location'])[:100],
    race_date
))

race_id = cursor.fetchone()[0]
print(f"✅ Race ID: {race_id}")

# Insert drivers and teams
driver_count = 0
for driver_code in race.drivers:
    try:
        driver_info = race.get_driver(driver_code)
        team_name = driver_info.get('TeamName', 'Unknown')[:100]
        
        # Insert team
        team_id = team_name.replace(' ', '_').upper()[:10]
        cursor.execute("DELETE FROM teams WHERE team_id = %s", (team_id,))
        cursor.execute("INSERT INTO teams (team_id, team_name) VALUES (%s, %s) ON CONFLICT DO NOTHING", 
                      (team_id, team_name))
        
        # Insert driver
        driver_number = clean_value(driver_info.get('DriverNumber', 0))
        cursor.execute("DELETE FROM drivers WHERE driver_id = %s", (driver_code,))
        cursor.execute("""
            INSERT INTO drivers (driver_id, driver_name, team_id, driver_number)
            VALUES (%s, %s, %s, %s)
        """, (driver_code, driver_info['FullName'][:100], team_id, driver_number))
        
        # Get race result
        result = race.results[race.results['Abbreviation'] == driver_code]
        if not result.empty:
            cursor.execute("DELETE FROM race_results WHERE race_id = %s AND driver_id = %s", 
                          (race_id, driver_code))
            cursor.execute("""
                INSERT INTO race_results (race_id, driver_id, final_position, points, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                race_id, 
                driver_code, 
                clean_value(result['Position'].iloc[0]),
                clean_value(result['Points'].iloc[0]),
                str(result['Status'].iloc[0])[:50]
            ))
        
        driver_count += 1
        if driver_count % 5 == 0:
            print(f"   Processed {driver_count} drivers...")
            
    except Exception as e:
        print(f"   Warning: Could not process {driver_code}: {e}")
        continue

print(f"✅ Processed {driver_count} drivers")

# Insert lap times
laps = race.laps
lap_count = 0
batch = []
batch_size = 500

for _, lap in laps.iterrows():
    try:
        # Convert lap time to seconds
        lap_time = None
        if lap['LapTime']:
            lap_time = float(lap['LapTime'].total_seconds())
        
        # Get tire compound (clean it)
        compound = None
        if 'Compound' in lap and lap['Compound']:
            compound = str(lap['Compound']).strip().upper()
            if 'SOFT' in compound:
                compound = 'SOFT'
            elif 'MEDIUM' in compound:
                compound = 'MEDIUM'
            elif 'HARD' in compound:
                compound = 'HARD'
            elif 'INTER' in compound:
                compound = 'INTERMEDIATE'
            elif 'WET' in compound:
                compound = 'WET'
            else:
                compound = compound[:10]
        
        batch.append((
            race_id,
            lap['Driver'],
            clean_value(lap['LapNumber']),
            lap_time,
            clean_value(lap['Position']),
            compound,
            clean_value(lap.get('TyreLife', None))
        ))
        lap_count += 1
        
        if len(batch) >= batch_size:
            cursor.executemany("""
                INSERT INTO lap_times (race_id, driver_id, lap_number, lap_time, position, tire_compound, tire_life)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            print(f"   Inserted {lap_count} laps...")
            batch = []
            
    except Exception as e:
        print(f"   Skipping lap {lap.get('LapNumber', '?')}: {e}")
        continue

# Insert remaining laps
if batch:
    cursor.executemany("""
        INSERT INTO lap_times (race_id, driver_id, lap_number, lap_time, position, tire_compound, tire_life)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, batch)
    conn.commit()

print(f"✅ Inserted {lap_count} lap times")

# Final commit
conn.commit()
cursor.close()
conn.close()

print("\n" + "="*50)
print("🎉 SUCCESS! Data ingestion complete!")
print("="*50)
print(f"   Race: 2023 Monaco Grand Prix")
print(f"   Drivers: {driver_count}")
print(f"   Laps: {lap_count}")
print("\n📊 Run your dashboard:")
print("   cd dashboard")
print("   streamlit run strategy_dashboard.py")