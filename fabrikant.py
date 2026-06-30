"""
Tender Helper v1.5
Fabrikant source module.
"""

import html
import re

import requests


SOURCE_NAME = "Фабрикант"
URL = "https://www.fabrikant.ru/procedure/search"


def clean_text(value):
    """
    Clean escaped text from Next.js stream.
    """
    if not value:
        return ""

    text = value
    text = text.replace("\\u0026", "&")
    text = text.replace('\\"', '"')
    text = text.replace("\\\\", "\\")
    text = html.unescape(text)
    return text.strip()


def parse_price(value):
    """
    Convert Fabrikant price text to float.
    """
    if not value:
        return 0.0

    text = clean_text(str(value))

    if "цена не указана" in text.lower():
        return 0.0

    cleaned = text.replace("\xa0", " ")
    cleaned = cleaned.replace(",", ".")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_card_blocks(html_text):
    """
    Extract approximate trade card blocks from Next.js stream.
    """
    pattern = r'data-id\\":[0-9]+.*?(?=data-id\\":[0-9]+|TradeListMore|</script>)'

    return [
        match.group(0)
        for match in re.finditer(pattern, html_text, flags=re.DOTALL)
    ]


def extract_tenders_from_html(html_text):
    """
    Extract tenders from Fabrikant HTML.
    """
    blocks = extract_card_blocks(html_text)
    results = []

    for block in blocks:
        number_match = re.search(r'\\"№ \\",([0-9]+)(?:,\\"-([0-9]+)\\")?', block)
        url_match = re.search(r'\\"url\\":\\"(https://fabrikant\.ru[^\\"]+)', block)
        name_match = re.search(r'\\"name\\":\\"(.*?)\\",\\"action\\"', block)
        organizer_match = re.search(r'\\"Организатор\\".*?\\"name\\":\\"(.*?)\\"', block, re.DOTALL)
        deadline_match = re.search(
            r'Дата окончания при[ёе]ма заявок.*?\\"children\\":\\"([0-9]{2}\.[0-9]{2}\.[0-9]{4} [0-9]{2}:[0-9]{2})\\"',
            block,
            re.DOTALL,
        )
        price_match = re.search(
            r'\\"children\\":\[\\"([0-9 ][0-9 ]*)\\",\[\\"\\$\\",\\"span\\".*?\\"children\\":\[\\"\\",\\"([0-9]{2})\\",\\" \\",\\"RUB\\"\]',
            block,
            re.DOTALL,
        )

        if not name_match or not url_match:
            continue

        number = ""
        if number_match:
            number = number_match.group(1)
            if number_match.group(2):
                number = f"{number}-{number_match.group(2)}"

        title = clean_text(name_match.group(1))
        url = clean_text(url_match.group(1))

        # Some URLs are escaped and may be cut before query params.
        url = url.replace("\\u0026", "&")

        customer = ""
        if organizer_match:
            customer = clean_text(organizer_match.group(1))

        deadline = None
        if deadline_match:
            deadline = deadline_match.group(1)

        price = 0.0
        if price_match:
            rub = price_match.group(1).replace(" ", "")
            kop = price_match.group(2)
            price = parse_price(f"{rub},{kop}")

        results.append(
            {
                "title": title,
                "price": price,
                "customer": customer,
                "url": url,
                "source": SOURCE_NAME,
                "number": number,
                "deadline": deadline,
                "region": None,
                "relevance_score": 80,
            }
        )

    return results


def search_fabrikant_tenders(category=None, region=None, budget=None, limit=5):
    """
    Search tenders on Fabrikant.

    Current version:
    - loads public search page
    - extracts trade cards from Next.js stream
    - filters by category in title locally
    - returns Tender Helper normalized items
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    items = extract_tenders_from_html(response.text)

    results = []
    category_text = (category or "").lower().strip()

    for tender in items:
        if category_text and category_text not in tender["title"].lower():
            continue

        if budget:
            price = tender.get("price") or 0.0
            if price and price > float(budget):
                continue

        results.append(tender)

        if len(results) >= limit:
            break

    return results