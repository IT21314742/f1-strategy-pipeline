import fastapi as ff1
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os

# Enable cache
ff1.Cache.enable_cache('f1_cache')

class F1DataPipeline:
    def __init__(self):
        self.conn = psycopg2.connect(
            
        )