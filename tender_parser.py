import re

from regions import REGION_ALIASES


def parse_tender_query(text):
    text_lower = text.lower()

    region = None
    budget = None
    category = text

    for alias, region_name in REGION_ALIASES.items():
        if alias in text_lower:
            region = region_name

            category = re.sub(
                alias,
                "",
                category,
                flags=re.IGNORECASE,
            )

            break

    budget_match = re.search(
        r"до\s+(\d+)\s*(млн|миллион|миллиона|миллионов)",
        text_lower,
    )

    if budget_match:
        budget_number = int(budget_match.group(1))
        budget = budget_number * 1_000_000

        category = re.sub(
            r"до\s+\d+\s*(млн|миллион|миллиона|миллионов)",
            "",
            category,
            flags=re.IGNORECASE,
        )

    category = " ".join(category.split())

    return {
        "category": category,
        "region": region,
        "budget": budget,
    }


def format_parsed_query(parsed_data):
    region = parsed_data["region"] or "не определён"
    budget = parsed_data["budget"]

    if budget:
        budget_text = f"до {budget:,} ₽".replace(",", " ")
    else:
        budget_text = "не определён"

    return (
        "Я понял запрос:\n\n"
        f"Категория: {parsed_data['category']}\n"
        f"Регион: {region}\n"
        f"Бюджет: {budget_text}\n\n"
        "Запрос сохранён ✅\n\n"
        "Что можно сделать дальше?\n\n"
        "1. Найти похожие тендеры\n"
        "2. Объяснить, какие тендеры подойдут\n"
        "3. Показать сохранённые запросы"
    )