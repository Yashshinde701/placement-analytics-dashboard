"""Load data/students.csv into the `students` table created by schema.sql.

Needs PLACEMENT_DB_URL for an account with INSERT (and DELETE, for --replace).
Run it with a loader account, not the read-only dashboard account.
"""
import argparse
import os
import sys

from sqlalchemy import create_engine, text

from dataset import DATA_PATH, DB_URL_ENV, _read_csv, validate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replace", action="store_true",
                    help="delete all existing rows first (otherwise rows are appended)")
    args = ap.parse_args()

    url = os.getenv(DB_URL_ENV)
    if not url:
        sys.exit(f"{DB_URL_ENV} is not set")

    df = validate(_read_csv(DATA_PATH))
    engine = create_engine(url)
    try:
        with engine.begin() as conn:  # one transaction: all rows land or none do
            if args.replace:
                conn.execute(text("DELETE FROM students"))
            df.to_sql("students", conn, if_exists="append", index=False, chunksize=500)
    finally:
        engine.dispose()
    print(f"Loaded {len(df)} students")


if __name__ == "__main__":
    main()
