import re

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://zakupki.gov.ru"


def clean_text(text):
    return " ".join(text.split())


def extract_price(text):
    match = re.search(r"Начальная цена\s+([\d\s]+,\d{2})\s+₽", text)

    if not match:
        return None

    price_text = match.group(1)
    price_number = price_text.replace(" ", "").replace(",", ".")

    return float(price_number)


def test_zakupki_parse():
    url = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

    params = {
        "searchString": "ремонт кровли",
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
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(".search-registry-entry-block")

    print("Найдено карточек:", len(cards))

    for index, card in enumerate(cards[:5], start=1):
        text = clean_text(card.get_text(" ", strip=True))

        law = "223-ФЗ" if "223-ФЗ" in text else "44-ФЗ" if "44-ФЗ" in text else "Не определён"

        number_link = None

        for link in card.select("a"):
            link_text = clean_text(link.get_text(" ", strip=True))
            href = link.get("href")

            if link_text.startswith("№") and href:
                if href.startswith("/"):
                    href = BASE_URL + href

                number_link = {
                    "number": link_text,
                    "url": href,
                }
                break

        customer = "Не найден"
        customer_match = re.search(r"Заказчик\s+(.+?)\s+Начальная цена", text)
        if customer_match:
            customer = customer_match.group(1)

        price = extract_price(text)

        title = "Не найден"
        title_match = re.search(r"Объект закупки\s+(.+?)\s+Заказчик", text)
        if title_match:
            title = title_match.group(1)

        print("=" * 80)
        print("Закон:", law)

        if number_link:
            print("Номер:", number_link["number"])
            print("Ссылка:", number_link["url"])
        else:
            print("Номер: не найден")
            print("Ссылка: не найдена")

        print("Объект закупки:", title)
        print("Заказчик:", customer)
        print("Цена:", price)


if __name__ == "__main__":
    test_zakupki_parse()