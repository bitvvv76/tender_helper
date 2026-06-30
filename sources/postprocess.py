"""
Tender Helper v1.5.1
Postprocess module.

Goal:
- normalize tenders after all sources
- remove duplicates
- calculate relevance score
- sort results
- keep collector output stable
"""


def make_dedup_key(tender):
    """
    Build stable duplicate key for tender.

    Priority:
    1. number
    2. url
    3. title + customer
    """
    number = str(tender.get("number") or "").strip().lower()
    url = str(tender.get("url") or "").strip().lower()
    title = str(tender.get("title") or "").strip().lower()
    customer = str(tender.get("customer") or "").strip().lower()

    if number:
        return f"number:{number}"

    if url:
        return f"url:{url}"

    return f"title_customer:{title}:{customer}"


def normalize_price(tender):
    """
    Make price field predictable.
    """
    value = tender.get("price")

    if value is None:
        tender["price"] = 0.0
        return tender

    try:
        tender["price"] = float(value)
    except (TypeError, ValueError):
        tender["price"] = 0.0

    return tender


def normalize_tender(tender):
    """
    Normalize one tender item.
    """
    normalized = dict(tender)

    normalized.setdefault("title", "")
    normalized.setdefault("price", 0.0)
    normalized.setdefault("customer", "")
    normalized.setdefault("url", "")
    normalized.setdefault("source", "")
    normalized.setdefault("number", "")
    normalized.setdefault("deadline", None)
    normalized.setdefault("region", None)
    normalized.setdefault("relevance_score", 0)

    normalize_price(normalized)

    return normalized


def deduplicate_tenders(tenders):
    """
    Remove duplicate tenders while preserving order.
    """
    seen = set()
    unique = []

    for tender in tenders:
        key = make_dedup_key(tender)

        if key in seen:
            continue

        seen.add(key)
        unique.append(tender)

    return unique


def calculate_query_match_score(title, category=None):
    """
    Calculate how well tender title matches search category/query.
    """
    category_text = str(category or "").lower().strip()

    if not category_text:
        return 0

    category_words = [
        word.strip()
        for word in category_text.split()
        if len(word.strip()) >= 3
    ]

    if category_text in title:
        return 25

    if not category_words:
        return 0

    matched_words = 0

    for word in category_words:
        if word in title:
            matched_words += 1

    if matched_words == len(category_words):
        return 20

    if matched_words > 0:
        return 10

    return 0


def calculate_relevance_score(tender, category=None):
    """
    Calculate tender relevance score from 0 to 100.

    Scoring v3.1:
    - query/category match is the main factor
    - exact query match does not automatically give 100
    - price, deadline, source and metadata are smaller bonuses
    - score scale should be more spread out
    """
    score = 0

    title = str(tender.get("title") or "").lower()
    price = tender.get("price") or 0
    deadline = tender.get("deadline")
    source = str(tender.get("source") or "").lower()
    customer = str(tender.get("customer") or "").strip()
    number = str(tender.get("number") or "").strip()
    category_text = str(category or "").lower().strip()

    # 1. Query/category match — main factor
    if category_text:
        category_words = [
            word.strip()
            for word in category_text.split()
            if len(word.strip()) >= 3
        ]

        if category_text in title:
            score += 30
        elif category_words:
            matched_words = 0

            for word in category_words:
                if word in title:
                    matched_words += 1

            if matched_words == len(category_words):
                score += 25
            elif matched_words > 0:
                score += 12
    else:
        score += 5

    # 2. Title quality
    if title:
        score += 10

    if len(title) >= 30:
        score += 5

    if len(title) >= 80:
        score += 3

    # 3. Important tender words
    important_words = [
        "поставка",
        "ремонт",
        "строительство",
        "капитальный ремонт",
        "услуги",
        "работы",
        "монтаж",
        "оборудование",
    ]

    for word in important_words:
        if word in title:
            score += 8
            break

    # 4. Price quality
    if price and price > 0:
        score += 8

    if price and price >= 500000:
        score += 4

    if price and price >= 3000000:
        score += 3

    if price and price >= 20000000:
        score += 2

    # 5. Deadline exists
    if deadline:
        score += 8

    # 6. Customer exists
    if customer:
        score += 4

    # 7. Number exists
    if number:
        score += 4

    # 8. Source bonus
    reliable_sources = [
        "еис",
        "сбер",
        "росэлторг",
        "газпромбанк",
        "тэк",
        "фабрикант",
    ]

    for source_name in reliable_sources:
        if source_name in source:
            score += 3
            break

    if score > 100:
        score = 100

    if score < 0:
        score = 0

    return score


def apply_scoring(tenders, category=None):
    """
    Apply relevance score to every tender.
    """
    scored = []

    for tender in tenders:
        item = dict(tender)
        item["relevance_score"] = calculate_relevance_score(
            item,
            category=category,
        )
        scored.append(item)

    return scored


def sort_tenders(tenders):
    """
    Sort tenders by relevance score first, then by price.
    """
    return sorted(
        tenders,
        key=lambda item: (
            item.get("relevance_score") or 0,
            item.get("price") or 0,
        ),
        reverse=True,
    )


def postprocess_tenders(tenders, category=None):
    """
    Main postprocess pipeline.
    """
    normalized = [normalize_tender(tender) for tender in tenders]
    unique = deduplicate_tenders(normalized)
    scored = apply_scoring(unique, category=category)
    sorted_items = sort_tenders(scored)

    return sorted_items