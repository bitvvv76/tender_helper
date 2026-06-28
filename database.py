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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            price REAL,
            customer TEXT,
            url TEXT,
            source TEXT,
            number TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS last_found_tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            position INTEGER,
            title TEXT,
            price REAL,
            customer TEXT,
            url TEXT,
            source TEXT,
            number TEXT
        )
        """
    )

    cursor.execute("PRAGMA table_info(last_found_tenders)")
    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if "deadline" not in columns:
        cursor.execute(
            """
            ALTER TABLE last_found_tenders
            ADD COLUMN deadline TEXT
            """
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_text TEXT NOT NULL,
            category TEXT,
            region TEXT,
            budget INTEGER,
            last_seen_number TEXT,
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

def get_top_queries(limit=10):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            category,
            COUNT(*) as count
        FROM search_queries
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
        LIMIT ?
        """,
        (limit,),
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

def save_tender(
    user_id,
    title,
    price,
    customer,
    url,
    source,
    number,
):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM saved_tenders
        WHERE user_id = ? AND number = ?
        LIMIT 1
        """,
        (user_id, number),
    )

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return False

    cursor.execute(
        """
        INSERT INTO saved_tenders (
            user_id,
            title,
            price,
            customer,
            url,
            source,
            number,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            title,
            price,
            customer,
            url,
            source,
            number,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    connection.commit()
    connection.close()

    return True

def get_saved_tenders(user_id, limit=10):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            title,
            price,
            customer,
            url,
            source,
            number,
            created_at
        FROM saved_tenders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows

def make_tender_dedupe_key(tender):
    number = (tender.get("number") or "").strip()
    url = (tender.get("url") or "").strip()
    title = (tender.get("title") or "").strip().lower()
    price = tender.get("price")

    if number:
        return f"number:{number}"

    if url:
        return f"url:{url}"

    return f"title_price:{title}:{price}"


def save_last_found_tenders(user_id, tenders):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM last_found_tenders
        WHERE user_id = ?
        """,
        (user_id,),
    )

    now = datetime.now().isoformat(timespec="seconds")
    seen_keys = set()
    unique_tenders = []

    for tender in tenders:
        dedupe_key = make_tender_dedupe_key(tender)

        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)
        unique_tenders.append(tender)

    for position, tender in enumerate(unique_tenders, start=1):
        cursor.execute(
            """
            INSERT INTO last_found_tenders (
                user_id,
                position,
                title,
                price,
                customer,
                url,
                source,
                number,
                deadline,
                status,
                created_at,
                updated_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                position,
                tender.get("title"),
                tender.get("price"),
                tender.get("customer"),
                tender.get("url"),
                tender.get("source"),
                tender.get("number"),
                tender.get("deadline"),
                "active",
                now,
                now,
                now,
            ),
        )

    connection.commit()
    connection.close()

def get_last_found_tender(user_id, position):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            title,
            price,
            customer,
            url,
            source,
            number
        FROM last_found_tenders
        WHERE user_id = ? AND position = ?
        LIMIT 1
        """,
        (user_id, position),
    )

    row = cursor.fetchone()

    connection.close()

    return row

def delete_saved_tender(user_id, position):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM saved_tenders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1 OFFSET ?
        """,
        (user_id, position - 1),
    )

    row = cursor.fetchone()

    if not row:
        connection.close()
        return False

    tender_id = row[0]

    cursor.execute(
        """
        DELETE FROM saved_tenders
        WHERE id = ? AND user_id = ?
        """,
        (tender_id, user_id),
    )

    connection.commit()
    connection.close()

    return True

def clear_saved_tenders(user_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM saved_tenders
        WHERE user_id = ?
        """,
        (user_id,),
    )

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count

def save_subscription(user_id, original_text, category, region, budget):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM subscriptions
        WHERE user_id = ?
          AND category = ?
          AND IFNULL(region, '') = IFNULL(?, '')
          AND IFNULL(budget, 0) = IFNULL(?, 0)
        LIMIT 1
        """,
        (user_id, category, region, budget),
    )

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return False

    cursor.execute(
        """
        INSERT INTO subscriptions (
            user_id,
            original_text,
            category,
            region,
            budget,
            last_seen_number,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            original_text,
            category,
            region,
            budget,
            None,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    connection.commit()
    connection.close()

    return True

def get_subscriptions(user_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            original_text,
            category,
            region,
            budget,
            created_at
        FROM subscriptions
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows

def delete_subscription(user_id, position):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM subscriptions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1 OFFSET ?
        """,
        (user_id, position - 1),
    )

    row = cursor.fetchone()

    if not row:
        connection.close()
        return False

    subscription_id = row[0]

    cursor.execute(
        """
        DELETE FROM subscriptions
        WHERE id = ? AND user_id = ?
        """,
        (subscription_id, user_id),
    )

    connection.commit()
    connection.close()

    return True

def clear_subscriptions(user_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM subscriptions
        WHERE user_id = ?
        """,
        (user_id,),
    )

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count

def get_subscriptions_for_check(user_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category,
            region,
            budget,
            last_seen_number
        FROM subscriptions
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows

def update_subscription_last_seen(subscription_id, tender_number):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE subscriptions
        SET last_seen_number = ?
        WHERE id = ?
        """,
        (tender_number, subscription_id),
    )

    connection.commit()
    connection.close()

def get_all_subscriptions():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            category,
            region,
            budget,
            last_seen_number
        FROM subscriptions
        ORDER BY user_id
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows