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
        team_id = team_name.replace(" ","_").upper()[:10]
        
        self.cursor.execute(
            
        )
