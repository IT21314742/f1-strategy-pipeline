import psycopg2

try:
    conn = psycopg2,connect(
        host="localhost",
        port=5432,
        database="f1_strategy",
        user="f1_analyst",
        password="f1_strategy_2025"
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    
    print(f"✅ Connected to PostgreSQL successfully!")
    print(f"'📦 Version: {version[0]}")
    
    cursor.close()
    conn.close()
    
    