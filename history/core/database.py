import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()


def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        cursor_factory=RealDictCursor  # supaya hasil cursor berupa dict, bukan tuple
    )


def get_db():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()