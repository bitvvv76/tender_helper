import re

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://zakupki.gov.ru"


def clean_text(text):
    text = " ".join(text.split())

    replacements = {
        "кровл и": "кровли",
        "защит ы": "защиты",
        "защит ной": "защитной",
        "беспилотн ого": "беспилотного",
        "беспилотн ых": "беспилотных",
        "воздушн ого": "воздушного",
        "воздушн ых": "воздушных",
        "суд на": "судна",
        "суд ов": "судов",
        "БАШКОРТОСТА Н": "БАШКОРТОСТАН",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def extract_price(text):
    match = re.search(r"Начальная цена\s+([\d\s]+,\d{2})\s+₽", text)

    if not match:
        return None

    price_text = match.group(1)
    price_number = price_text.replace(" ", "").replace(",", ".")

    return float(price_number)

def get_region_keywords(region):
    if not region:
        return []

    region_lower = region.lower()

    if region_lower == "удмуртия":
        return ["удмуртия", "удмуртская республика", "ижевск"]

    if region_lower == "татарстан":
        return ["татарстан", "республика татарстан", "казань"]

    if region_lower == "башкортостан":
        return ["башкортостан", "республика башкортостан", "уфа"]

    if region_lower == "пермский край":
        return ["пермский край", "пермь"]

    return [region_lower]

def get_search_words(category):
    ignored_words = {
        "и", "в", "на", "по", "для", "от", "до", "с", "со",
        "закупка", "поставка", "работы", "услуги"
    }

    words = category.lower().split()

    normalized_words = []

    for word in words:
        if word.startswith("нефтебаз"):
            normalized_words.append("нефтебаз")
        elif word.startswith("кровл"):
            normalized_words.append("кровл")
        elif word.startswith("защит"):
            normalized_words.append("защит")
        elif word.startswith("бпла"):
            normalized_words.append("бпла")
        else:
            normalized_words.append(word)

    words = normalized_words

    return [
        word
        for word in words
        if len(word) > 2 and word not in ignored_words
    ]


def calculate_relevance_score(card_text, category):
    search_words = get_search_words(category)

    if not search_words:
        return 0

    text = card_text.lower()

    score = 0

    for word in search_words:
        if word in text:
            score += 1

    return score


def search_real_tenders(category, region=None, budget=None, limit=5):
    url = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

    search_string = category

    if region:
        search_string = f"{category} {region}"

    params = {
        "searchString": search_string,
        "morphology": "on",
        "pageNumber": 1,
        "sortDirection": "false",
        "recordsPerPage": 10,
        "showLotsInfoHidden": "false",
        "fz44": "on",
        "fz223": "on",
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select(".search-registry-entry-block")

    tenders = []

    for card in cards:
        text = clean_text(card.get_text(" ", strip=True))

        region_keywords = get_region_keywords(region)

        if region_keywords:
            text_lower = text.lower()

            if not any(keyword in text_lower for keyword in region_keywords):
                continue

        law = "223-ФЗ" if "223-ФЗ" in text else "44-ФЗ" if "44-ФЗ" in text else "Не определён"

        number = "Не найден"
        tender_url = "Ссылка не найдена"

        for link in card.select("a"):
            link_text = clean_text(link.get_text(" ", strip=True))
            href = link.get("href")

            if link_text.startswith("№") and href:
                number = link_text

                if href.startswith("/"):
                    href = BASE_URL + href

                tender_url = href
                break

        customer = "Не найден"
        customer_match = re.search(r"Заказчик\s+(.+?)\s+Начальная цена", text)
        if customer_match:
            customer = customer_match.group(1)

        title = "Не найден"
        title_match = re.search(r"Объект закупки\s+(.+?)\s+Заказчик", text)
        if title_match:
            title = title_match.group(1)

        price = extract_price(text)

        relevance_score = calculate_relevance_score(
            card_text=text,
            category=category,
        )
        search_words = get_search_words(category)

        if len(search_words) >= 2 and relevance_score < 2:
            continue

        if len(search_words) == 1 and relevance_score == 0:
            continue

        if budget and price and price > budget:
            continue

        if title == "Не найден" or customer == "Не найден":
            continue

        tender = {
            "title": title,
            "region": region or "Регион не указан",
            "price": price or 0,
            "customer": customer,
            "url": tender_url,
            "source": f"ЕИС {law}",
            "number": number,
            "relevance_score": relevance_score,
        }

        tenders.append(tender)

        if len(tenders) >= limit:
            break
    tenders.sort(key=lambda tender: tender.get("relevance_score", 0), reverse=True)

    return tenders


def format_real_tenders(tenders):
    if not tenders:
        return (
            "Реальные тендеры пока не найдены.\n\n"
            "Попробуйте изменить запрос:\n"
            "• ремонт кровли\n"
            "• поставка окон\n"
            "• ремонт дороги\n\n"
            "Также можно увеличить бюджет или убрать регион."
        )

    lines = ["🌐 Я нашёл реальные тендеры из ЕИС:\n"]

    for index, tender in enumerate(tenders, start=1):
        price_text = f"{tender['price']:,.2f} ₽".replace(",", " ")

        lines.append(
            f"{index}. {tender['title']}\n"
            f"📌 Номер: {tender['number']}\n"
            f"📍 Регион/поиск: {tender['region']}\n"
            f"💰 Цена: {price_text}\n"
            f"🏢 Заказчик: {tender['customer']}\n"
            f"🔗 Ссылка: {tender['url']}\n"
            f"Источник: {tender['source']}\n"
        )

    return "\n".join(lines)