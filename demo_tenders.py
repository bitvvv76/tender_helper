DEMO_TENDERS = [
    {
        "title": "Ремонт кровли здания школы",
        "category_keywords": ["ремонт", "кровли", "кровля"],
        "region": "Удмуртия",
        "price": 4_800_000,
        "customer": "Муниципальное учреждение",
    },
    {
        "title": "Капитальный ремонт кровли административного здания",
        "category_keywords": ["ремонт", "кровли", "кровля"],
        "region": "Удмуртия",
        "price": 3_900_000,
        "customer": "Администрация района",
    },
    {
        "title": "Поставка пластиковых окон для школы",
        "category_keywords": ["поставка", "окон", "окна"],
        "region": "Татарстан",
        "price": 3_600_000,
        "customer": "Государственное бюджетное учреждение",
    },
    {
        "title": "Поставка оконных блоков для детского сада",
        "category_keywords": ["поставка", "окон", "окна"],
        "region": "Татарстан",
        "price": 4_200_000,
        "customer": "Муниципальный заказчик",
    },
    {
        "title": "Ремонт автомобильной дороги местного значения",
        "category_keywords": ["ремонт", "дороги", "дорога"],
        "region": "Удмуртия",
        "price": 2_700_000,
        "customer": "Дорожное управление",
    },
    {
        "title": "Строительство детской спортивной площадки",
        "category_keywords": ["строительство", "площадки", "площадка"],
        "region": "Башкортостан",
        "price": 6_500_000,
        "customer": "Администрация муниципального района",
    },
]


def find_demo_tenders(category, region=None, budget=None, limit=3):
    category_lower = category.lower()
    results = []

    for tender in DEMO_TENDERS:
        if region and tender["region"] != region:
            continue

        if budget and tender["price"] > budget:
            continue

        matched_keywords = 0

        for keyword in tender["category_keywords"]:
            if keyword in category_lower:
                matched_keywords += 1

        if matched_keywords >= 2:
            results.append(tender)
            
    return results[:limit]


def format_demo_tenders(tenders):
    if not tenders:
        return (
            "Похожих демо-тендеров пока не найдено.\n\n"
            "Попробуйте другой запрос, например:\n"
            "ремонт кровли Удмуртия до 5 млн"
        )

    lines = [
        "Я нашёл похожие демо-тендеры:\n"
    ]

    for index, tender in enumerate(tenders, start=1):
        price_text = f"{tender['price']:,} ₽".replace(",", " ")

        lines.append(
            f"{index}. {tender['title']}\n"
            f"Регион: {tender['region']}\n"
            f"Цена: {price_text}\n"
            f"Заказчик: {tender['customer']}\n"
        )

    lines.append(
        "Важно: это демо-примеры для MVP. "
        "Позже подключим реальные источники тендеров."
    )

    return "\n".join(lines)