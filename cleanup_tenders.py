import argparse
import sqlite3
from datetime import datetime


DB_NAME = "tenders.db"


def get_now():
    return datetime.now().isoformat(timespec="seconds")


def cleanup_tenders(dry_run=True):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    now = get_now()

    cursor.execute(
        """
        SELECT
            id,
            title,
            number,
            deadline,
            status
        FROM last_found_tenders
        WHERE COALESCE(status, 'active') = 'active'
          AND (
                deadline IS NULL
                OR TRIM(deadline) = ''
                OR date(deadline) < date('now', 'localtime')
          )
        ORDER BY
            id ASC
        """
    )

    rows = cursor.fetchall()

    print("=== Tender cleanup ===")
    print(f"Dry run: {dry_run}")
    print(f"Found old/invalid active tenders: {len(rows)}")

    for row in rows:
        tender_id, title, number, deadline, status = row

        print(
            f"- id={tender_id} | number={number} | "
            f"deadline={deadline} | status={status} | title={title}"
        )

    if dry_run:
        print("\nNo changes applied.")
        connection.close()
        return len(rows)

    cursor.execute(
        """
        UPDATE last_found_tenders
        SET
            status = 'archived',
            updated_at = ?
        WHERE COALESCE(status, 'active') = 'active'
          AND (
                deadline IS NULL
                OR TRIM(deadline) = ''
                OR date(deadline) < date('now', 'localtime')
          )
        """,
        (now,),
    )

    archived_count = cursor.rowcount

    connection.commit()
    connection.close()

    print(f"\nArchived tenders: {archived_count}")

    return archived_count


def main():
    parser = argparse.ArgumentParser(
        description="Archive old or invalid tenders."
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply cleanup. Without this flag, script runs in dry-run mode.",
    )

    args = parser.parse_args()

    cleanup_tenders(
        dry_run=not args.apply
    )


if __name__ == "__main__":
    main()