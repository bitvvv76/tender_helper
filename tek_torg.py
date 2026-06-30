"""
Tender Helper v1.5
TEK-Torg source module.
"""

import json
import re

import requests
from bs4 import BeautifulSoup


SOURCE_NAME = "ТЭК-Торг"
URL = "https://www.tektorg.ru/procedures"


def parse_price(value):
    """
    Convert TEK-Torg price value to float.
    If price is not set, return 0.0.
    """
    if value is None:
        return 0.0

    text = str(value)

    if "не установлена" in text.lower():
        return 0.0

    cleaned = text.replace("\xa0", " ")
    cleaned = cleaned.replace(",", ".")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_next_data(html):
    """
    Extract Next.js __NEXT_DATA__ JSON from HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})

    if not script or not script.string:
        return {}

    return json.loads(script.string)


def extract_items(data):
    """
    Extract procedures list from Next.js initial Redux state.
    """
    try:
        return (
            data["props"]["pageProps"]["initialReduxState"]
            ["listingProcedures"]["data"]
        )
    except (KeyError, TypeError):
        return []


def normalize_tender(item):
    """
    Convert TEK-Torg procedure item to Tender Helper format.
    """
    dates = item.get("dates") or {}

    return {
        "title": item.get("title") or "",
        "price": parse_price(item.get("sumPrice")),
        "customer": item.get("organizerName") or "",
        "url": item.get("etpLink") or URL,
        "source": SOURCE_NAME,
        "number": item.get("registryNumber") or str(item.get("id") or ""),
        "deadline": dates.get("dateEndRegistration"),
        "region": None,
        "relevance_score": 80,
    }


def search_tek_torg_tenders(category=None, region=None, budget=None, limit=5):
    """
    Search tenders on TEK-Torg.

    Current version:
    - loads public procedures page
    - extracts Next.js data
    - filters by category in title locally
    - returns Tender Helper normalized items
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    data = load_next_data(response.text)
    items = extract_items(data)

    results = []

    category_text = (category or "").lower().strip()

    for item in items:
        tender = normalize_tender(item)

        if category_text:
            title = tender["title"].lower()
            if category_text not in title:
                continue

        if budget:
            price = tender.get("price") or 0.0
            if price and price > float(budget):
                continue

        results.append(tender)

        if len(results) >= limit:
            break

    return results