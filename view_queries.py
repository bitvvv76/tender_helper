import sqlite3


DB_NAME = "tenders.db"


def view_queries():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            original_text,
            category,
            region,
            budget,
            created_at
        FROM search_queries
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    if not rows:
        print("В базе пока нет сохранённых запросов.")
    else:
        print("Сохранённые запросы:")
        print("-" * 60)

        for row in rows:
            query_id, user_id, original_text, category, region, budget, created_at = row

            print(f"ID: {query_id}")
            print(f"User ID: {user_id}")
            print(f"Исходный текст: {original_text}")
            print(f"Категория: {category}")
            print(f"Регион: {region}")
            print(f"Бюджет: {budget}")
            print(f"Дата: {created_at}")
            print("-" * 60)

    connection.close()


if __name__ == "__main__":
    view_queries()