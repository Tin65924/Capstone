"""One-command demo seeder for the system demonstration video.

Usage:
    venv\\Scripts\\python.exe dev/seed_demo.py

Runs, in dependency order (each step is idempotent / self-resetting):
    1. seed_books.py ................. catalog + accessions (top-up only)
    2. dev/seed_requests_defense.py .. demo users (all roles) + requests
    3. dev/seed_analytics_100.py ..... 100 circulation rows for analytics
    4. dev/seed_demo_supplement.py ... procurement, reservations, fines,
                                       inventory sessions, audit rows

Ends with a verification count summary. Fails fast on the first error.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

STEPS = [
    ([PY, "seed_books.py"], "catalog + accessions"),
    ([PY, "dev/seed_requests_defense.py"], "demo users + requests"),
    ([PY, "dev/seed_analytics_100.py"], "analytics circulation rows"),
    ([PY, "dev/seed_demo_supplement.py"], "procurement/reservations/fines/inventory/audit"),
]

SUMMARY_SQL = """
SELECT 'users', COUNT(*) FROM user_accounts
UNION ALL SELECT 'books', COUNT(*) FROM book_catalog
UNION ALL SELECT 'accessions', COUNT(*) FROM accession_log
UNION ALL SELECT 'requests', COUNT(*) FROM request_records
UNION ALL SELECT 'procurement', COUNT(*) FROM procurement_log
UNION ALL SELECT 'loans', COUNT(*) FROM circulation_records
UNION ALL SELECT 'reservations', COUNT(*) FROM reservation_queue
"""


def main():
    for cmd, label in STEPS:
        print(f"--- {label}: {' '.join(cmd)} ---", flush=True)
        subprocess.run(cmd, cwd=ROOT, check=True)
    print("--- verification counts ---")
    import os

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    import psycopg2

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(SUMMARY_SQL)
    for name, count in cur.fetchall():
        print(f"{name:12s} {count}")
    conn.close()
    print("demo seed complete")


if __name__ == "__main__":
    main()
