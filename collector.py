import argparse
from datetime import datetime

from database import save_collected_tenders
from sources.loader import search_all_sources


COLLECTOR_USER_ID = 0


DEFAULT_QUERIES = [
    {
        "category": "ремонт кровли",
        "region": None,
        "budget": None,
        "limit": 5,
    },
    {
        "category": "ремонт дороги",
        "region": None,
        "budget": None,
        "limit": 5,
    },
    {
        "category": "поставка окон",
        "region": None,
        "budget": None,
        "limit": 5,
    },
    {
        "category": "поставка мебели",
        "region": None,
        "budget": None,
        "limit": 5,
    },
    {
        "category": "капитальный ремонт",
        "region": None,
        "budget": None,
        "limit": 5,
    },
    {
        "category": "строительные работы",
        "region": None,
        "budget": None,
        "limit": 5,
    },
]


def collect_tenders(category, region=None, budget=None, limit=5, dry_run=True):
    print("=== Tender collector ===")
    print(f"Time: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Category: {category}")
    print(f"Region: {region}")
    print(f"Budget: {budget}")
    print(f"Limit: {limit}")
    print(f"Dry run: {dry_run}")

    tenders = search_all_sources(
        category=category,
        region=region,
        budget=budget,
        limit=limit,
    )

    print(f"Всего найдено: {len(tenders)}")

    for index, tender in enumerate(tenders, start=1):
        score = tender.get("relevance_score", 0)

        print(
            f"{index}. score={score} | "
            f"{tender.get('number')} | "
            f"{tender.get('price')} | "
            f"{tender.get('deadline')} | "
            f"{tender.get('title')}"
        )

    if dry_run:
        print("\nNo changes applied.")
        return len(tenders)

    result = save_collected_tenders(
        tenders,
        user_id=COLLECTOR_USER_ID,
    )

    print("\nSave result:")
    print(f"Saved: {result['saved']}")
    print(f"Updated: {result['updated']}")
    print(f"Skipped duplicates: {result['skipped']}")
    print(f"Total unique: {result['total']}")

    return result["total"]


def collect_all_tenders(dry_run=True):
    print("=== Tender collector: all queries ===")
    print(f"Time: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Dry run: {dry_run}")
    print(f"Queries: {len(DEFAULT_QUERIES)}")

    all_tenders = []

    for query in DEFAULT_QUERIES:
        category = query["category"]
        region = query["region"]
        budget = query["budget"]
        limit = query["limit"]

        print("\n----------------------------------------")
        print(f"Category: {category}")
        print(f"Region: {region}")
        print(f"Budget: {budget}")
        print(f"Limit: {limit}")

        tenders = search_all_sources(
            category=category,
            region=region,
            budget=budget,
            limit=limit,
        )

        print(f"Всего найдено: {len(tenders)}")

        for tender in tenders:
            all_tenders.append(tender)

    print("\n=== Summary ===")
    print(f"Total found before save: {len(all_tenders)}")

    if dry_run:
        print("No changes applied.")
        return len(all_tenders)

    result = save_collected_tenders(
        all_tenders,
        user_id=COLLECTOR_USER_ID,
    )

    print("Save result:")
    print(f"Saved: {result['saved']}")
    print(f"Updated: {result['updated']}")
    print(f"Skipped duplicates: {result['skipped']}")
    print(f"Total unique: {result['total']}")

    return result["total"]


def main():
    parser = argparse.ArgumentParser(
        description="Collect tenders and save them to local database."
    )

    parser.add_argument("--category", default="ремонт кровли")
    parser.add_argument("--region", default=None)
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true")

    args = parser.parse_args()

    if args.all:
        collect_all_tenders(dry_run=not args.apply)
    else:
        collect_tenders(
            category=args.category,
            region=args.region,
            budget=args.budget,
            limit=args.limit,
            dry_run=not args.apply,
        )


if __name__ == "__main__":
    main()