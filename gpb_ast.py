import json
import subprocess
from bs4 import BeautifulSoup


BASE_URL = "https://etpgpb.ru"
URL = "https://etpgpb.ru/procedures/"


def fetch_html():
    """
    Газпромбанк АСТ на Windows может падать через requests из-за SSL.
    Поэтому используем curl.exe --ssl-no-revoke.
    На VPS позже проверим отдельно.
    """
    result = subprocess.run(
        ["curl.exe", "--ssl-no-revoke", URL],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=40,
    )

    if result.returncode != 0:
        print("GPB CURL ERROR:", result.stderr)
        return ""

    return result.stdout


def resolve_value(data, value):
    if isinstance(value, int) and 0 <= value < len(data):
        resolved = data[value]

        if isinstance(resolved, (str, int, float, bool)) or resolved is None:
            return resolved

        if isinstance(resolved, list):
            return [resolve_value(data, item) for item in resolved]

        return resolved

    return value


def normalize_url(url):
    if not url:
        return ""

    if isinstance(url, str) and url.startswith("http"):
        return url

    if isinstance(url, str) and url.startswith("/"):
        return BASE_URL + url

    return url


def parse_gpb_tenders(html):
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NUXT_DATA__"})

    if not script:
        print("GPB: NUXT DATA NOT FOUND")
        return []

    data = json.loads(script.text)

    tenders = []
    seen_numbers = set()

    def walk(obj):
        if isinstance(obj, dict):
            keys = set(obj.keys())

            if {
                "registry_number",
                "title",
                "platform_url",
                "company_name",
                "end_registration",
            }.issubset(keys):
                registry_number = resolve_value(data, obj.get("registry_number"))

                if registry_number and registry_number not in seen_numbers:
                    seen_numbers.add(registry_number)

                    title = resolve_value(data, obj.get("title"))
                    platform_url = resolve_value(data, obj.get("platform_url"))
                    truncated_path = resolve_value(data, obj.get("truncated_path"))
                    company_name = resolve_value(data, obj.get("company_name"))
                    amount = resolve_value(data, obj.get("amount"))
                    currency_name = resolve_value(data, obj.get("currency_name"))
                    date_published = resolve_value(data, obj.get("date_published"))
                    end_registration = resolve_value(data, obj.get("end_registration"))
                    lot_regions = resolve_value(data, obj.get("lot_regions"))
                    procedure_type_name = resolve_value(data, obj.get("procedure_type_name"))

                    url = normalize_url(platform_url or truncated_path)

                    tenders.append({
                        "source": "Газпромбанк АСТ",
                        "number": str(registry_number),
                        "title": title or "",
                        "price": str(amount or ""),
                        "customer": company_name or "",
                        "url": url,
                        "deadline": end_registration or "",
                        "region": str(lot_regions or ""),
                        "type": procedure_type_name or "",
                    })

            for value in obj.values():
                walk(value)

        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return tenders


def get_gpb_tenders(limit=10):
    html = fetch_html()

    if not html:
        return []

    tenders = parse_gpb_tenders(html)
    return tenders[:limit]
def search_gpb_tenders(category, region=None, budget=None, limit=5):
    """
    Поиск тендеров Газпромбанк АСТ для collector.py.
    Пока базовая версия: берём свежие процедуры с площадки,
    затем мягко фильтруем по категории, региону и бюджету.
    """
    tenders = get_gpb_tenders(limit=50)

    filtered = []

    category_lower = category.lower() if category else ""
    region_lower = region.lower() if region else ""

    for tender in tenders:
        title = str(tender.get("title", "")).lower()
        tender_region = str(tender.get("region", "")).lower()

        if category_lower and category_lower not in title:
            continue

        if region_lower and region_lower not in tender_region:
            continue

        if budget:
            try:
                price = float(str(tender.get("price", "0")).replace(",", "."))
                if price > float(budget):
                    continue
            except ValueError:
                pass

        filtered.append(tender)

        if len(filtered) >= limit:
            break

    return filtered

if __name__ == "__main__":
    tenders = get_gpb_tenders(limit=10)

    print("GPB FOUND:", len(tenders))

    for tender in tenders:
        print("=" * 80)
        print("SOURCE:", tender["source"])
        print("NUMBER:", tender["number"])
        print("TITLE:", tender["title"])
        print("TYPE:", tender["type"])
        print("CUSTOMER:", tender["customer"])
        print("PRICE:", tender["price"])
        print("REGION:", tender["region"])
        print("DEADLINE:", tender["deadline"])
        print("URL:", tender["url"])