import json
import html
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

BASE_URL = "https://www.sberbank-ast.ru"


def get_value(tag):
    if tag.name == "input":
        return tag.get("value") or ""

    if tag.name == "select":
        option = tag.select_one("option[selected]")
        if option:
            return option.get_text(strip=True)

        option = tag.select_one("option")
        return option.get_text(strip=True) if option else ""

    return tag.get_text(strip=True)


def build_xml_from_node(tag):
    result = ""

    for child in tag.find_all(recursive=False):
        content = child.get("content")

        if content and content.startswith("leaf:"):
            name = content.replace("leaf:", "")
            value = get_value(child)
            result += f"<{name}>{value}</{name}>"

        elif content and content.startswith("node:"):
            name = content.replace("node:", "")
            inner = build_xml_from_node(child)
            result += f"<{name}>{inner}</{name}>"

        else:
            result += build_xml_from_node(child)

    return result


def get_text(parent, tag_name):
    item = parent.find(tag_name)
    if item is None or item.text is None:
        return ""
    return item.text.strip()

def normalize_sber_deadline(raw_deadline):
    if not raw_deadline:
        return None

    raw_deadline = raw_deadline.strip()

    formats = [
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(raw_deadline, fmt).date().isoformat()
        except ValueError:
            continue

    return raw_deadline


def parse_sber_response(response_text, limit=5):
    outer = json.loads(response_text)

    if outer.get("result") != "success":
        return []

    data = json.loads(outer["data"])

    table_xml = data.get("tableXml", "")
    table_xml = html.unescape(table_xml)

    root = ET.fromstring(table_xml)

    tenders = []

    for hit in root.findall("hits"):
        source = hit.find("_source")

        if source is None:
            continue

        title = get_text(source, "purchName") or get_text(source, "BidName")
        price_text = get_text(source, "purchAmount")
        customer = get_text(source, "OrgName")
        url = get_text(source, "objectHrefTerm")
        number = get_text(source, "purchCodeTerm")
        deadline = normalize_sber_deadline(get_text(source, "RequestDate"))
        tender_source = get_text(source, "SourceTerm")

        if not title or not url:
            continue

        try:
            price = float(price_text.replace(",", ".")) if price_text else 0
        except ValueError:
            price = 0

        tender = {
            "title": title,
            "region": "Регион не указан",
            "price": price,
            "customer": customer,
            "url": url,
            "source": f"Сбер А {tender_source}".strip(),
            "number": number,
            "deadline": deadline,
            "relevance_score": 70,
        }

        tenders.append(tender)

        if len(tenders) >= limit:
            break

    return tenders


def search_sber_tenders(category, region=None, budget=None, limit=5):
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"{BASE_URL}/purchaseList.aspx",
        "Origin": BASE_URL,
        "X-Requested-With": "XMLHttpRequest",
    }

    page_url = f"{BASE_URL}/purchaseList.aspx"

    page_response = session.get(
        page_url,
        headers=headers,
        timeout=20,
    )

    if page_response.status_code != 200:
        return []

    soup = BeautifulSoup(page_response.text, "html.parser")

    query = category
    if region:
        query = f"{category} {region}"

    search_input = soup.select_one("#searchInput")
    if search_input:
        search_input["value"] = query

    xml_container = soup.select_one("#xmlContainer")

    if not xml_container:
        return []

    xml_data = build_xml_from_node(xml_container)

    search_url = f"{BASE_URL}/SearchQuery.aspx?name=Main"

    data = {
        "xmlData": xml_data,
        "orgId": "0",
        "targetPageCode": "ESPurchaseList",
        "PID": "0",
    }

    response = session.post(
        search_url,
        headers=headers,
        data=data,
        timeout=30,
    )

    if response.status_code != 200:
        return []

    tenders = parse_sber_response(response.text, limit=limit)

    if budget:
        tenders = [
            tender for tender in tenders
            if tender.get("price", 0) and tender["price"] <= budget
        ]

    return tenders[:limit]


if __name__ == "__main__":
    results = search_sber_tenders(
        category="ремонт",
        region=None,
        budget=None,
        limit=5,
    )

    print("Found:", len(results))

    for index, tender in enumerate(results, start=1):
        print("=" * 80)
        print(f"{index}. {tender['title']}")
        print("Price:", tender["price"])
        print("Customer:", tender["customer"])
        print("Number:", tender["number"])
        print("Deadline:", tender["deadline"])
        print("Source:", tender["source"])
        print("URL:", tender["url"])