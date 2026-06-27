import os
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv




app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
ENV_PATH = PROJECT_DIR / ".env"

load_dotenv(ENV_PATH)

INDEX_HTML = BASE_DIR / "templates" / "index.html"
STATIC_DIR = BASE_DIR / "static"

LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "tender_site.log"

LOG_DIR.mkdir(
    exist_ok=True
)

logger = logging.getLogger("tender_site")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

# База данных основного проекта Tender Helper
DB_PATH = os.getenv("TENDER_DB_PATH")

if not DB_PATH:
    raise RuntimeError(
        "Переменная TENDER_DB_PATH не найдена в файле .env"
    )

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not ADMIN_TOKEN:
    raise RuntimeError(
        "Переменная ADMIN_TOKEN не найдена в файле .env"
    )


def check_admin_token(token):
    if token != ADMIN_TOKEN:
        logger.warning(
            "Попытка доступа к debug-маршруту без правильного токена"
        )

        return JSONResponse(
            status_code=403,
            content={
                "error": "Доступ запрещён"
            },
        )

    return None


# =========================================================
# ГЛАВНАЯ СТРАНИЦА
# =========================================================
@app.get("/")
def home():
    return FileResponse(INDEX_HTML)

# =========================================================
# АКТУАЛЬНЫЕ ТЕНДЕРЫ ИЗ БАЗЫ
# =========================================================
@app.get("/tenders")
def get_tenders():
    database_path = Path(DB_PATH)

    if not database_path.exists():
        return JSONResponse(
            status_code=503,
            content={
                "count": 0,
                "tenders": [],
                "error": "База данных тендеров временно недоступна.",
            },
        )

    connection = None

    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                tender.title,
                tender.price,
                tender.customer,
                tender.url,
                tender.source,
                tender.number,
                tender.deadline
            FROM last_found_tenders AS tender

            INNER JOIN (
                SELECT
                    MAX(id) AS latest_id
                FROM last_found_tenders

                WHERE
                    deadline IS NOT NULL
                    AND TRIM(deadline) != ''
                    AND date(deadline) >= date(
                        'now',
                        'localtime'
                    )

                GROUP BY
                    COALESCE(
                        NULLIF(TRIM(number), ''),
                        NULLIF(TRIM(url), ''),
                        title
                    )
            ) AS active_unique_tenders

            ON tender.id = active_unique_tenders.latest_id

            ORDER BY
                date(tender.deadline) ASC,
                tender.id DESC

            LIMIT 20
            """
        )

        rows = cursor.fetchall()

        tenders = []

        for row in rows:
            tenders.append(
                {
                    "title": row["title"] or "Без названия",
                    "price": (
                        row["price"]
                        if row["price"] is not None
                        else 0
                    ),
                    "customer": (
                        row["customer"]
                        or "Заказчик не указан"
                    ),
                    "url": row["url"] or "",
                    "source": (
                        row["source"]
                        or "Источник не указан"
                    ),
                    "number": (
                        row["number"]
                        or "Номер не указан"
                    ),
                    "deadline": row["deadline"] or "",
                }
            )

        return {
            "count": len(tenders),
            "tenders": tenders,
            "error": None,
        }

    except sqlite3.Error as error:
        logger.exception("Ошибка базы данных в /tenders")

        return JSONResponse(
            status_code=503,
            content={
                "count": 0,
                "tenders": [],
                "error": (
                    "Не удалось загрузить тендеры. "
                    "Попробуйте обновить страницу позже."
                ),
            },
        )

    except Exception as error:
        logger.exception("Непредвиденная ошибка в /tenders")

        return JSONResponse(
            status_code=500,
            content={
                "count": 0,
                "tenders": [],
                "error": "Произошла внутренняя ошибка сервера.",
            },
        )

    finally:
        if connection is not None:
            connection.close()

# =========================================================
# ПОИСК РЕАЛЬНЫХ ТЕНДЕРОВ ИЗ ЕИС
# =========================================================
@app.get("/search")
def search_tenders(
    query: str,
    region: str | None = None,
    budget: float | None = None,
    limit: int = 5,
):
    database_path = Path(DB_PATH)

    if not database_path.exists():
        return JSONResponse(
            status_code=503,
            content={
                "count": 0,
                "tenders": [],
                "error": "База данных тендеров временно недоступна.",
            },
        )

    try:
        if not query or len(query.strip()) < 3:
            return JSONResponse(
                status_code=400,
                content={
                    "count": 0,
                    "tenders": [],
                    "error": "Введите поисковый запрос минимум из 3 символов.",
                },
            )

        if limit < 1:
            limit = 1

        if limit > 20:
            limit = 20

        search_text = f"%{query.strip().lower()}%"

        sql = """
            SELECT
                title,
                price,
                customer,
                url,
                source,
                number,
                deadline
            FROM last_found_tenders
            WHERE
                (
                    lower(COALESCE(title, '')) LIKE ?
                    OR lower(COALESCE(customer, '')) LIKE ?
                    OR lower(COALESCE(number, '')) LIKE ?
                    OR lower(COALESCE(source, '')) LIKE ?
                )
        """
        params = [
            search_text,
            search_text,
            search_text,
            search_text,
        ]

        if region and region.strip():
            region_text = f"%{region.strip().lower()}%"

            sql += """
                AND (
                    lower(COALESCE(title, '')) LIKE ?
                    OR lower(COALESCE(customer, '')) LIKE ?
                    OR lower(COALESCE(source, '')) LIKE ?
                )
            """

            params.extend(
                [
                    region_text,
                    region_text,
                    region_text,
                ]
            )

        if budget is not None:
            sql += """
                AND price <= ?
            """

            params.append(budget)

        sql += """
            ORDER BY
                CASE
                    WHEN deadline IS NULL OR TRIM(deadline) = '' THEN 1
                    ELSE 0
                END,
                date(deadline) ASC,
                price ASC
            LIMIT ?
        """

        params.append(limit)

        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        finally:
            connection.close()

        tenders = []

        for row in rows:
            tenders.append(
                {
                    "title": row["title"] or "Без названия",
                    "price": (
                        row["price"]
                        if row["price"] is not None
                        else 0
                    ),
                    "customer": row["customer"] or "Заказчик не указан",
                    "url": row["url"] or "",
                    "source": row["source"] or "Источник не указан",
                    "number": row["number"] or "Номер не указан",
                    "deadline": row["deadline"] or "",
                }
            )

        return {
            "count": len(tenders),
            "tenders": tenders,
            "error": None,
        }

    except Exception:
        logger.exception("Ошибка поиска тендеров в /search")

        return JSONResponse(
            status_code=500,
            content={
                "count": 0,
                "tenders": [],
                "error": "Не удалось выполнить поиск тендеров по базе.",
            },
        )
    
# =========================================================
# ДИАГНОСТИКА БАЗЫ
# =========================================================
@app.get("/debug-db")
def debug_db(token: str = ""):
    access_error = check_admin_token(token)

    if access_error:
        return access_error

    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )

        tables = [
            row[0]
            for row in cursor.fetchall()
        ]

        return {
            "database": DB_PATH,
            "tables": tables,
        }

    finally:
        connection.close()

# =========================================================
# СТРУКТУРА ТАБЛИЦЫ
# =========================================================
@app.get("/debug-tender-columns")
def debug_tender_columns(token: str = ""):
    access_error = check_admin_token(token)

    if access_error:
        return access_error

    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute(
            "PRAGMA table_info(last_found_tenders)"
        )

        columns = cursor.fetchall()

        return {
            "columns": [
                {
                    "position": column[0],
                    "name": column[1],
                    "type": column[2],
                    "not_null": column[3],
                    "default": column[4],
                    "primary_key": column[5],
                }
                for column in columns
            ]
        }

    finally:
        connection.close()