import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.roseltorg.ru"


def parse_price(text):
    match = re.search(r"([\d\s]+,\d{2})\s*₽", text)

    if not match:
        return 0

    raw_price = match.group(1)
    raw_price = raw_price.replace(" ", "").replace(",", ".")

    try:
        return float(raw_price)
    except ValueError:
        return 0


def parse_deadline(text):
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+в\s+(\d{2}:\d{2})", text)

    if not match:
        return None

    raw_deadline = f"{match.group(1)} {match.group(2)}"

    try:
        return datetime.strptime(raw_deadline, "%d.%m.%Y %H:%M").date().isoformat()
    except ValueError:
        return None


def parse_number(text):
    match = re.search(r"\b(\d{19})\b", text)

    if not match:
        return ""

    return match.group(1)


def parse_region(text):
    match = re.search(
        r"\b(\d{2}\.\s+[А-Яа-яЁё\s\-]+?(?:область|край|республика|Республика|округ|Москва|Санкт-Петербург|Севастополь))",
        text,
    )

    if not match:
        return "Регион не указан"

    return match.group(1).strip()


def parse_customer(text):
    if "Организатор" not in text:
        return ""

    after = text.split("Организатор", 1)[1]

    stop_words = [
        "Прием заявок",
        "Приём заявок",
        "Ожидание приема",
        "Ожидание приёма",
        "Работа комиссии",
        "Процедура",
        "СМП и СОНО",
        "Ещё +",
    ]

    for word in stop_words:
        if word in after:
            after = after.split(word, 1)[0]

    after = re.sub(r"\s+", " ", after).strip()

    return after


def parse_roseltorg_card(card):
    title_link = card.select_one(".search-results__subject a")
    if not title_link:
        return None

    title = title_link.get_text(" ", strip=True)
    href = title_link.get("href") or ""
    url = urljoin(BASE_URL, href)

    number = card.get("data-feature-favorite-lots-procedure-number") or ""

    region_tag = card.select_one(".search-results__region p")
    region = region_tag.get_text(" ", strip=True) if region_tag else "Регион не указан"

    customer_tag = card.select_one(".search-results__customer p a")
    customer = customer_tag.get_text(" ", strip=True) if customer_tag else ""

    price_tag = card.select_one(".search-results__sum p.desktop")
    price_text = price_tag.get_text(" ", strip=True) if price_tag else card.get_text(" ", strip=True)
    price = parse_price(price_text)

    deadline_tag = card.select_one(".search-results__time")
    deadline_text = deadline_tag.get_text(" ", strip=True) if deadline_tag else card.get_text(" ", strip=True)
    deadline = parse_deadline(deadline_text)

    if not title or not url:
        return None

    return {
        "title": title,
        "region": region,
        "price": price,
        "customer": customer,
        "url": url,
        "source": "Росэлторг 44-ФЗ",
        "number": number,
        "deadline": deadline,
        "relevance_score": 70,
    }

def search_roseltorg_tenders(category, region=None, budget=None, limit=5):
    query = category
    if region:
        query = f"{category} {region}"

    params = {
        "sale": "1",
        "source[]": "1",
        "place": "44fz",
        "query_field": query,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    response = None

    for attempt in range(1, 4):
        try:
            response = requests.get(
                f"{BASE_URL}/procedures/search_ajax",
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                break

            print(f"Росэлторг: попытка {attempt}, status={response.status_code}")

        except requests.RequestException as error:
            print(f"Росэлторг: ошибка запроса, попытка {attempt}: {error}")

    if response is None or response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(".search-results__item.autoload-post")

    tenders = []

    for card in cards:
        tender = parse_roseltorg_card(card)

        if not tender:
            continue

        if budget and tender.get("price", 0) and tender["price"] > budget:
            continue

        tenders.append(tender)

        if len(tenders) >= limit:
            break

    return tenders


if __name__ == "__main__":
    results = search_roseltorg_tenders(
        category="ремонт",
        region=None,
        budget=None,
        limit=5,
    )

    print("Found:", len(results))

    for index, tender in enumerate(results, start=1):
        print("=" * 80)
        print(f"{index}. {tender['title']}")
        print("Region:", tender["region"])
        print("Price:", tender["price"])
        print("Customer:", tender["customer"])
        print("Number:", tender["number"])
        print("Deadline:", tender["deadline"])
        print("Source:", tender["source"])
        print("URL:", tender["url"])