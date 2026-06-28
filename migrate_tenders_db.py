import sqlite3
from datetime import datetime


DB_NAME = "tenders.db"


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_missing(cursor, table_name, column_name, column_sql):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_sql}
            """
        )
        print(f"OK: added column {column_name}")
    else:
        print(f"SKIP: column {column_name} already exists")


def migrate_last_found_tenders():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    add_column_if_missing(
        cursor,
        "last_found_tenders",
        "status",
        "status TEXT DEFAULT 'active'",
    )

    add_column_if_missing(
        cursor,
        "last_found_tenders",
        "created_at",
        "created_at TEXT",
    )

    add_column_if_missing(
        cursor,
        "last_found_tenders",
        "updated_at",
        "updated_at TEXT",
    )

    add_column_if_missing(
        cursor,
        "last_found_tenders",
        "last_seen_at",
        "last_seen_at TEXT",
    )

    cursor.execute(
        """
        UPDATE last_found_tenders
        SET status = 'active'
        WHERE status IS NULL OR status = ''
        """
    )

    cursor.execute(
        """
        UPDATE last_found_tenders
        SET created_at = ?
        WHERE created_at IS NULL OR created_at = ''
        """,
        (now,),
    )

    cursor.execute(
        """
        UPDATE last_found_tenders
        SET updated_at = ?
        WHERE updated_at IS NULL OR updated_at = ''
        """,
        (now,),
    )

    cursor.execute(
        """
        UPDATE last_found_tenders
        SET last_seen_at = ?
        WHERE last_seen_at IS NULL OR last_seen_at = ''
        """,
        (now,),
    )

    connection.commit()

    cursor.execute("PRAGMA table_info(last_found_tenders)")
    columns = cursor.fetchall()

    print("\nCurrent last_found_tenders columns:")
    for column in columns:
        print(column)

    connection.close()


if __name__ == "__main__":
    migrate_last_found_tenders()