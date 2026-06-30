"""
Tender Helper v1.5
Manual test for dynamic sources loader.
"""

from sources.loader import search_all_sources


def main():
    category = "поставка"
    limit = 3

    print("=== Tender Helper v1.5 sources loader test ===")
    print("Category:", category)
    print("Limit:", limit)
    print("-" * 40)

    results = search_all_sources(
        category=category,
        limit=limit,
    )

    print("-" * 40)
    print("TOTAL:", len(results))

    for index, tender in enumerate(results, start=1):
        number = tender.get("number") or tender.get("tender_number") or ""
        price = tender.get("price")
        deadline = tender.get("deadline")
        title = tender.get("title")

        print(f"{index}. {number} | {price} | {deadline} | {title}")


if __name__ == "__main__":
    main()