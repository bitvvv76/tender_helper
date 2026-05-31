DEMO_TENDERS = [
    {
        "title": "Ремонт кровли здания школы",
        "category_keywords": ["ремонт", "кровли", "кровля", "школа"],
        "region": "Удмуртия",
        "price": 4_800_000,
        "customer": "Муниципальное учреждение",
    },
    {
        "title": "Капитальный ремонт кровли административного здания",
        "category_keywords": ["ремонт", "кровли", "кровля", "здание"],
        "region": "Удмуртия",
        "price": 3_900_000,
        "customer": "Администрация района",
    },
    {
        "title": "Текущий ремонт крыши детского сада",
        "category_keywords": ["ремонт", "крыши", "кровля", "детский", "сад"],
        "region": "Удмуртия",
        "price": 2_400_000,
        "customer": "Муниципальный заказчик",
    },
    {
        "title": "Поставка пластиковых окон для школы",
        "category_keywords": ["поставка", "окон", "окна", "школа"],
        "region": "Татарстан",
        "price": 3_600_000,
        "customer": "Государственное бюджетное учреждение",
    },
    {
        "title": "Поставка оконных блоков для детского сада",
        "category_keywords": ["поставка", "окон", "окна", "оконные", "блоки"],
        "region": "Татарстан",
        "price": 4_200_000,
        "customer": "Муниципальный заказчик",
    },
    {
        "title": "Замена окон в здании администрации",
        "category_keywords": ["замена", "окон", "окна", "администрация"],
        "region": "Удмуртия",
        "price": 1_900_000,
        "customer": "Администрация муниципального образования",
    },
    {
        "title": "Ремонт автомобильной дороги местного значения",
        "category_keywords": ["ремонт", "дороги", "дорога", "автомобильная"],
        "region": "Удмуртия",
        "price": 2_700_000,
        "customer": "Дорожное управление",
    },
    {
        "title": "Ямочный ремонт дорог в населённом пункте",
        "category_keywords": ["ремонт", "дорог", "дороги", "ямочный"],
        "region": "Удмуртия",
        "price": 1_200_000,
        "customer": "Муниципальное казённое учреждение",
    },
    {
        "title": "Капитальный ремонт участка автомобильной дороги",
        "category_keywords": ["капитальный", "ремонт", "дороги", "дорога"],
        "region": "Татарстан",
        "price": 6_800_000,
        "customer": "Исполнительный комитет района",
    },
    {
        "title": "Строительство детской спортивной площадки",
        "category_keywords": ["строительство", "площадки", "площадка", "спортивная"],
        "region": "Башкортостан",
        "price": 6_500_000,
        "customer": "Администрация муниципального района",
    },
    {
        "title": "Устройство детской игровой площадки",
        "category_keywords": ["устройство", "детской", "площадки", "площадка"],
        "region": "Удмуртия",
        "price": 3_300_000,
        "customer": "Управление благоустройства",
    },
    {
        "title": "Поставка строительных материалов для ремонта здания",
        "category_keywords": ["поставка", "строительных", "материалов", "ремонт"],
        "region": "Удмуртия",
        "price": 900_000,
        "customer": "Бюджетное учреждение",
    },
    {
        "title": "Благоустройство территории возле школы",
        "category_keywords": ["благоустройство", "территории", "школа"],
        "region": "Удмуртия",
        "price": 2_100_000,
        "customer": "Администрация города",
    },
    {
        "title": "Ремонт помещений в здании поликлиники",
        "category_keywords": ["ремонт", "помещений", "здание", "поликлиника"],
        "region": "Татарстан",
        "price": 5_500_000,
        "customer": "Государственное учреждение здравоохранения",
    },
]


def calculate_match_score(tender, category_lower, region=None, budget=None):
    score = 0
    reasons = []

    matched_keywords = []

    for keyword in tender["category_keywords"]:
        if keyword in category_lower:
            matched_keywords.append(keyword)

    if matched_keywords:
        score += len(matched_keywords) * 10
        reasons.append(
            "совпадает по ключевым словам: " + ", ".join(matched_keywords)
        )

    if region and tender["region"] == region:
        score += 20
        reasons.append("совпадает регион")

    if budget:
        if tender["price"] <= budget:
            score += 15
            reasons.append("вписывается в бюджет")
        else:
            score -= 50
            reasons.append("выше указанного бюджета")

    return score, reasons


def find_demo_tenders(category, region=None, budget=None, limit=3):
    category_lower = category.lower()
    results = []

    for tender in DEMO_TENDERS:
        if region and tender["region"] != region:
            continue

        if budget and tender["price"] > budget:
            continue

        score, reasons = calculate_match_score(
            tender=tender,
            category_lower=category_lower,
            region=region,
            budget=budget,
        )

        if score > 0:
            tender_copy = tender.copy()
            tender_copy["score"] = score
            tender_copy["reasons"] = reasons
            results.append(tender_copy)

    results.sort(key=lambda tender: tender["score"], reverse=True)

    return results[:limit]


def format_demo_tenders(tenders):
    if not tenders:
        return (
            "Похожих демо-тендеров пока не найдено.\n\n"
            "Попробуйте уточнить запрос:\n"
            "• ремонт кровли Удмуртия до 5 млн\n"
            "• поставка окон Казань до 4 млн\n"
            "• ремонт дороги Ижевск до 3 млн\n\n"
            "Чем точнее указаны категория, регион и бюджет — "
            "тем лучше будет подбор."
        )

    lines = [
        "🔎 Я нашёл похожие демо-тендеры:\n"
    ]

    for index, tender in enumerate(tenders, start=1):
        price_text = f"{tender['price']:,} ₽".replace(",", " ")
        reasons_text = "; ".join(tender.get("reasons", []))

        lines.append(
            f"{index}. {tender['title']}\n"
            f"📍 Регион: {tender['region']}\n"
            f"💰 Цена: {price_text}\n"
            f"🏢 Заказчик: {tender['customer']}\n"
            f"✅ Почему подходит: {reasons_text}\n"
        )

    lines.append(
        "ℹ️ Это демо-подбор для MVP. "
        "На следующем этапе можно подключить реальные источники тендеров "
        "и показывать настоящие закупки со ссылками."
    )

    return "\n".join(lines)