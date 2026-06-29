import json
import subprocess
import platform
from bs4 import BeautifulSoup


BASE_URL = "https://etpgpb.ru"
URL = "https://etpgpb.ru/procedures/"


def fetch_html():
    """
    Получаем HTML страницы Газпромбанк АСТ.

    Windows:
    - используем curl.exe --ssl-no-revoke, потому что requests падает на SSL.

    Linux/VPS:
    - используем обычный curl -L.
    """

    system_name = platform.system().lower()

    if "windows" in system_name:
        command = [
            "curl.exe",
            "--ssl-no-revoke",
            "-L",
            URL,
        ]
    else:
        command = [
            "curl",
            "-L",
            URL,
        ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )

        if result.returncode != 0:
            print("GPB CURL ERROR:", result.stderr)
            return ""

        return result.stdout

    except Exception as e:
        print("GPB FETCH ERROR:", str(e))
        return ""


def safe_get(data, index, default=None):
    """
    Безопасно достаём значение из Nuxt-массива по индексу.
    """
    try:
        if isinstance(index, int) and 0 <= index < len(data):
            return data[index]
        return default
    except Exception:
        return default


def normalize_url(value):
    """
    Приводим ссылку к полному виду.
    """
    if not value:
        return BASE_URL

    value = str(value)

    if value.startswith("http"):
        return value

    if value.startswith("/"):
        return BASE_URL + value

    return BASE_URL + "/" + value


def normalize_price(value):
    """
    Приводим цену к числу, если возможно.
    """
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            return float(value)

        value = str(value)
        value = value.replace(" ", "")
        value = value.replace("\xa0", "")
        value = value.replace(",", ".")

        return float(value)
    except Exception:
        return None


def extract_nuxt_data(html):
    """
    Достаём JSON из <script id="__NUXT_DATA__">.
    """
    soup = BeautifulSoup(html, "html.parser")

    script = soup.find("script", {"id": "__NUXT_DATA__"})

    if not script:
        print("GPB ERROR: __NUXT_DATA__ not found")
        return None

    raw_json = script.string or script.get_text()

    if not raw_json:
        print("GPB ERROR: empty __NUXT_DATA__")
        return None

    try:
        return json.loads(raw_json)
    except Exception as e:
        print("GPB JSON ERROR:", str(e))
        return None


def find_procedure_objects(obj):
    """
    Рекурсивно ищем словари, похожие на тендеры Газпромбанк АСТ.
    """
    found = []

    if isinstance(obj, dict):
        keys = set(obj.keys())

        tender_keys = {
            "registry_number",
            "title",
            "platform_url",
            "company_name",
            "amount",
            "date_published",
            "end_registration",
        }

        if keys.intersection(tender_keys):
            if "registry_number" in keys or "title" in keys:
                found.append(obj)

        for value in obj.values():
            found.extend(find_procedure_objects(value))

    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_procedure_objects(item))

    return found


def resolve_nuxt_value(data, value):
    """
    В Nuxt JSON часто значения лежат как индексы массива.
    Эта функция пытается получить реальное значение.
    """
    if isinstance(value, int):
        resolved = safe_get(data, value, value)

        if resolved == value:
            return value

        if isinstance(resolved, int):
            second_resolved = safe_get(data, resolved, resolved)
            return second_resolved

        return resolved

    return value


def parse_gpb_tenders(html):
    """
    Парсим тендеры Газпромбанк АСТ из Nuxt JSON.
    """
    data = extract_nuxt_data(html)

    if not data:
        return []

    raw_objects = find_procedure_objects(data)

    tenders = []
    seen_numbers = set()

    for item in raw_objects:
        try:
            number = resolve_nuxt_value(data, item.get("registry_number"))
            title = resolve_nuxt_value(data, item.get("title"))
            url = resolve_nuxt_value(data, item.get("platform_url"))
            customer = resolve_nuxt_value(data, item.get("company_name"))
            price = resolve_nuxt_value(data, item.get("amount"))
            published = resolve_nuxt_value(data, item.get("date_published"))
            deadline = resolve_nuxt_value(data, item.get("end_registration"))

            if not number:
                continue

            if not title:
                continue

            if "поиск тендеров" in str(title).lower():
                continue

            number = str(number) if number else ""
            title = str(title) if title else "Без названия"

            if number in seen_numbers:
                continue

            seen_numbers.add(number)

            tender = {
                "title": title,
                "price": normalize_price(price),
                "customer": str(customer) if customer else "",
                "url": normalize_url(url),
                "source": "Газпромбанк АСТ",
                "number": number,
                "deadline": str(deadline) if deadline else "",
                "published": str(published) if published else "",
                "region": "",
                "relevance_score": 80,
            }

            tenders.append(tender)

        except Exception as e:
            print("GPB PARSE ITEM ERROR:", str(e))
            continue

    return tenders


def get_gpb_tenders(limit=10):
    """
    Получаем список тендеров Газпромбанк АСТ.
    """
    html = fetch_html()

    if not html:
        return []

    tenders = parse_gpb_tenders(html)

    return tenders[:limit]


def search_gpb_tenders(category=None, region=None, budget=None, limit=5):
    """
    Функция для collector.py.

    category — категория поиска
    region — регион
    budget — максимальный бюджет
    limit — лимит результатов
    """

    try:
        tenders = get_gpb_tenders(limit=50)

        filtered = []

        category_text = str(category).lower() if category else ""
        region_text = str(region).lower() if region else ""

        for tender in tenders:
            title = str(tender.get("title", "")).lower()
            customer = str(tender.get("customer", "")).lower()
            tender_region = str(tender.get("region", "")).lower()
            price = tender.get("price")

            if category_text:
                if category_text not in title and category_text not in customer:
                    continue

            if region_text:
                if region_text not in tender_region and region_text not in title and region_text not in customer:
                    continue

            if budget and price:
                try:
                    if float(price) > float(budget):
                        continue
                except Exception:
                    pass

            filtered.append(tender)

            if len(filtered) >= limit:
                break

        return filtered[:limit]

    except Exception as e:
        print("GPB SEARCH ERROR:", str(e))
        return []


if __name__ == "__main__":
    results = get_gpb_tenders(limit=10)

    print("GPB FOUND:", len(results))

    for tender in results:
        print("-" * 80)
        print("Номер:", tender.get("number"))
        print("Название:", tender.get("title"))
        print("Заказчик:", tender.get("customer"))
        print("Цена:", tender.get("price"))
        print("Дедлайн:", tender.get("deadline"))
        print("Ссылка:", tender.get("url"))