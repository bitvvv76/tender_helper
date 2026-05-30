import re

from regions import REGION_ALIASES


def parse_tender_query(text):
    text_lower = text.lower()

    region = None
    budget = None
    category = text

    for alias, region_name in REGION_ALIASES.items():
        alias_pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

        if re.search(alias_pattern, text_lower):
            region = region_name

            category = re.sub(
                alias_pattern,
                "",
                category,
                flags=re.IGNORECASE,
            )

            break

    budget_patterns = [
        (
            r"до\s+(\d+(?:[.,]\d+)?)\s*(миллионов|миллиона|миллион|млн)",
            1_000_000,
        ),
        (
            r"до\s+(\d+(?:[.,]\d+)?)\s*(тысяч|тысячи|тыс)",
            1_000,
        ),
        (
            r"до\s+(\d[\d\s]*)",
            1,
        ),
        (
            r"(\d+(?:[.,]\d+)?)\s*(миллионов|миллиона|миллион|млн)",
            1_000_000,
        ),
        (
            r"(\d+(?:[.,]\d+)?)\s*(тысяч|тысячи|тыс)",
            1_000,
        ),
        (
            r"\b(\d{6,})\b",
            1,
        ),
    ]

    for pattern, multiplier in budget_patterns:
        budget_match = re.search(pattern, text_lower)

        if budget_match:
            budget_text = budget_match.group(1).replace(",", ".").replace(" ", "")
            budget_number = float(budget_text)
            budget = int(budget_number * multiplier)

            category = re.sub(
                pattern,
                "",
                category,
                flags=re.IGNORECASE,
            )

            break
    category = re.sub(
        r"\b(в|во|по|на)\s*$",
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

def is_valid_tender_query(parsed_data):
    category = parsed_data["category"].strip().lower()
    region = parsed_data["region"]
    budget = parsed_data["budget"]

    bad_categories = [
        "",
        "?",
        "ок",
        "да",
        "нет",
        "найди",
        "найди что-нибудь",
        "тендер",
        "тендеры",
        "помощь",
        "привет",
    ]

    if category in bad_categories:
        return False

    if category.isdigit():
        return False

    if len(category) < 5:
        return False

    if not region and not budget and len(category.split()) < 2:
        return False

    return True