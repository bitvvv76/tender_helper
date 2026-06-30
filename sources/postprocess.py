"""
Tender Helper v1.5.1
Postprocess module.

Goal:
- normalize tenders after all sources
- remove duplicates
- sort results
- keep collector output stable
"""


def make_dedup_key(tender):
    """
    Build stable duplicate key for tender.

    Priority:
    1. source + number
    2. url
    3. title + customer
    """
    source = str(tender.get("source") or "").strip().lower()
    number = str(tender.get("number") or "").strip().lower()
    url = str(tender.get("url") or "").strip().lower()
    title = str(tender.get("title") or "").strip().lower()
    customer = str(tender.get("customer") or "").strip().lower()

    if source and number:
        return f"source_number:{source}:{number}"

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

    try:
        normalized["relevance_score"] = int(normalized.get("relevance_score") or 0)
    except (TypeError, ValueError):
        normalized["relevance_score"] = 0

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


def sort_tenders(tenders):
    """
    Sort tenders by relevance score first.
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
    sorted_items = sort_tenders(unique)

    return sorted_items