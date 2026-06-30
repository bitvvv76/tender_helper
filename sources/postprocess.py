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


def calculate_relevance_score(tender):
    """
    Calculate tender relevance score from 0 to 100.

    First scoring version:
    - title quality
    - important keywords
    - price presence
    - deadline presence
    - customer presence
    - source reliability
    """
    score = 0

    title = str(tender.get("title") or "").lower()
    price = tender.get("price") or 0
    deadline = tender.get("deadline")
    source = str(tender.get("source") or "").lower()
    customer = str(tender.get("customer") or "").strip()
    number = str(tender.get("number") or "").strip()

    # 1. Title quality
    if title:
        score += 20

    if len(title) >= 30:
        score += 10

    # 2. Important words in title
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
            score += 10
            break

    # 3. Price quality
    if price and price > 0:
        score += 20

    if price and price >= 500000:
        score += 10

    # 4. Deadline exists
    if deadline:
        score += 15

    # 5. Customer exists
    if customer:
        score += 10

    # 6. Number exists
    if number:
        score += 5

    # 7. Source bonus
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
            score += 5
            break

    if score > 100:
        score = 100

    if score < 0:
        score = 0

    return score


def apply_scoring(tenders):
    """
    Apply relevance score to every tender.
    """
    scored = []

    for tender in tenders:
        item = dict(tender)
        item["relevance_score"] = calculate_relevance_score(item)
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


def postprocess_tenders(tenders):
    """
    Main postprocess pipeline.
    """
    normalized = [normalize_tender(tender) for tender in tenders]
    unique = deduplicate_tenders(normalized)
    scored = apply_scoring(unique)
    sorted_items = sort_tenders(scored)

    return sorted_items