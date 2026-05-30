import sqlite3
from datetime import datetime


DB_NAME = "tenders.db"


def init_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS search_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_text TEXT NOT NULL,
            category TEXT,
            region TEXT,
            budget INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def save_search_query(user_id, original_text, category, region, budget):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO search_queries (
            user_id,
            original_text,
            category,
            region,
            budget,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            original_text,
            category,
            region,
            budget,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    connection.commit()
    connection.close()

def get_user_queries(user_id, limit=5):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            category,
            region,
            budget,
            created_at
        FROM search_queries
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows

def get_last_user_query(user_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            category,
            region,
            budget
        FROM search_queries
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    connection.close()

    return row