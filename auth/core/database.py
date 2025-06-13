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


def get_user_by_email(email: str):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM "users" WHERE email = %s', (email,))
            user = cursor.fetchone()
            return user
    finally:
        conn.close()


def create_user(name: str, email: str, hashed_password: str):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO "users" (name, email, password, created_at) VALUES (%s, %s, %s, %s)',
                (name, email, hashed_password, datetime.utcnow())
            )
            conn.commit()
    finally:
        conn.close()


def update_user_password(email: str, new_hashed_password: str):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE "users" SET password = %s WHERE email = %s',
                (new_hashed_password, email)
            )
            conn.commit()
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM "users" WHERE id = %s', (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()


def update_user_name(user_id: int, new_name: str):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE "users" SET name = %s WHERE id = %s',
                (new_name, user_id)
            )
            conn.commit()
    finally:
        conn.close()
