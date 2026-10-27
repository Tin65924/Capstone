"""Seed 100 deterministic circulation records for the Report & Analytics dashboard.

Usage:
    venv\\Scripts\\python.exe dev/seed_analytics_100.py [--reset | --no-reset]

What it does:
    1. Creates 12 seed users (9 Student + 3 Faculty) + borrowers across
       6 programs (id_numbers SEED100-001..., emails seed100_XX@mcst.edu.ph).
    2. Inserts exactly 100 circulation_records spread over the last 180 days
       with a mix of returned (~60) / active (~25) / overdue (~15), plus a
       few lost_flag rows — so every Analytics KPI has data:
       books_borrowed_per_program, utilization_rate, most_borrowed_titles,
       underutilized_titles, trends, top categories, by user type, overview.
    3. Tops up inventory_status (notes='SEED100') for accessions missing one,
       so the Condition Summary chart has data. Leaves ~10+ titles never
       borrowed so Underutilized Titles is non-empty.

Rerunnable: with --reset (the default) it deletes prior SEED100 rows
first (dependent tables -> circulation -> inventory notes='SEED100' ->
borrowers -> users). Pass --no-reset to append without cleaning.
"""
import argparse
import os
import random
import sys
from datetime import date, timedelta

SEED_TAG = "SEED100"
SEED_EMAIL_DOMAIN = "mcst.edu.ph"
N_CIRCULATION = 100
N_STUDENTS = 9
N_FACULTY = 3
PROGRAMS = ["BSIT", "BSBA", "BSED", "BEED", "BSHM", "BS Criminology"]
FIRST = ["Alex", "Maria", "Jose", "Ana", "Mark", "Liza", "John", "Rosa", "Paolo", "Nina", "Carlos", "Ella"]
LAST = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza", "Torres", "Ramos", "Aquino", "Navarro", "Salazar"]


def get_conn():
    """Open a psycopg2 connection from ``DATABASE_URL`` in ``.env``.

    Loads ``.env`` and connects with the ``DATABASE_URL`` value; exits
    the process with a message when it is unset, since every seed step
    needs the database.

    Returns:
        psycopg2 connection: Open connection (``autocommit=False`` is
            set by the caller); the caller owns close/commit.

    Side effects:
        Loads ``.env`` via ``load_dotenv``; calls ``sys.exit`` when
        ``DATABASE_URL`` is missing.
    """
    from dotenv import load_dotenv

    load_dotenv()
    import psycopg2

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        sys.exit("DATABASE_URL not set in .env")
    return psycopg2.connect(dsn)


def reset_seed(cur):
    """Delete prior SEED100 analytics rows in dependency order.

    Removes dependent reservation/notification/circulation rows for
    ``SEED100-*`` borrowers, then favorites/analytics/audit rows for
    ``seed100_*`` users, then ``inventory_status`` notes, borrowers and
    users. The ``'!'`` ESCAPE keeps the ``_`` in seed emails literal so
    only seed rows match.

    Args:
        cur: Open DB cursor on the seeding transaction.

    Returns:
        None.

    Side effects:
        DELETEs prior SEED100 rows across 8 tables; prints per-table
        row counts.
    """
    id_pattern = SEED_TAG + '-%%'
    # '_' is a LIKE wildcard: escape it so only seed emails match.
    email_pattern = SEED_TAG.lower() + '!_%%@' + SEED_EMAIL_DOMAIN
    cur.execute(
        "SELECT borrower_id FROM borrowers WHERE id_number LIKE %s", (id_pattern,)
    )
    bids = [r[0] for r in cur.fetchall()]
    cur.execute(
        "SELECT user_id FROM user_accounts WHERE email LIKE %s ESCAPE '!'",
        (email_pattern,),
    )
    uids = [r[0] for r in cur.fetchall()]
    if bids:
        cur.execute(
            "DELETE FROM reservation_queue WHERE borrower_id = ANY(%s)", (bids,)
        )
        print(f"removed {cur.rowcount} prior SEED100 reservation rows")
        cur.execute(
            "DELETE FROM notification_log WHERE recipient_id = ANY(%s)", (bids,)
        )
        print(f"removed {cur.rowcount} prior SEED100 notification rows")
        cur.execute(
            "DELETE FROM circulation_records WHERE borrower_id = ANY(%s)", (bids,)
        )
        print(f"removed {cur.rowcount} prior SEED100 circulation rows")
    if uids:
        cur.execute(
            "DELETE FROM user_favorites WHERE user_id = ANY(%s)", (uids,)
        )
        print(f"removed {cur.rowcount} prior SEED100 favorite rows")
        cur.execute(
            "DELETE FROM analytics_cache WHERE generated_by = ANY(%s)", (uids,)
        )
        print(f"removed {cur.rowcount} prior SEED100 analytics snapshots")
        cur.execute("DELETE FROM audit_trail WHERE user_id = ANY(%s)", (uids,))
        print(f"removed {cur.rowcount} prior SEED100 audit rows")
    cur.execute("DELETE FROM inventory_status WHERE notes = %s", (SEED_TAG,))
    print(f"removed {cur.rowcount} prior SEED100 inventory rows")
    cur.execute("DELETE FROM borrowers WHERE id_number LIKE %s", (id_pattern,))
    print(f"removed {cur.rowcount} prior SEED100 borrowers")
    cur.execute(
        "DELETE FROM user_accounts WHERE email LIKE %s ESCAPE '!'", (email_pattern,)
    )
    print(f"removed {cur.rowcount} prior SEED100 users")


def main(reset=True):
    """Seed 12 users and 100 deterministic circulation rows for Analytics.

    Creates 9 Student + 3 Faculty users/borrowers (``SEED100-*``), picks
    active accessions while sparing the last 10 titles (so the
    underutilized-titles KPI stays non-empty), weights 40% of loans
    onto a top-5 (so most-borrowed ranks clearly), spreads rows over
    180 days as ~60% returned / ~25% active / ~15% overdue, tops up
    ``inventory_status`` for the condition chart, and commits. Rolls
    back and re-raises on any error.

    Args:
        reset (bool): When True (default), delete prior SEED100 rows
            first; pass False (``--no-reset``) to append.

    Returns:
        None.

    Side effects:
        INSERTs users, borrowers, circulation and inventory rows;
        commits on success, rolls back on failure; prints a summary.
    """
    rng = random.Random(100)
    today = date.today()
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        if reset:
            reset_seed(cur)

        cur.execute("SELECT role_id, role_name FROM roles")
        roles = {name: rid for rid, name in cur.fetchall()}
        student_role = roles["Student"]
        faculty_role = roles["Faculty"]

        cur.execute(
            "SELECT user_id FROM user_accounts ORDER BY user_id LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            sys.exit("no users in DB — need at least one admin/librarian as processor")
        processed_by = row[0]

        # --- 1. seed users + borrowers -------------------------------------
        borrower_ids = []
        for i in range(N_STUDENTS + N_FACULTY):
            n = i + 1
            is_faculty = i >= N_STUDENTS
            email = f"seed100_{n:02d}@mcst.edu.ph"
            program = PROGRAMS[i % len(PROGRAMS)]
            cur.execute(
                """INSERT INTO user_accounts (email, oauth_sub, full_name, role_id, account_status)
                   VALUES (%s, %s, %s, %s, 'active') RETURNING user_id""",
                (
                    email,
                    f"seed100_oauth_{n:02d}",
                    f"{FIRST[i % len(FIRST)]} {LAST[(i * 3) % len(LAST)]}",
                    faculty_role if is_faculty else student_role,
                ),
            )
            uid = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO borrowers (user_id, id_number, department, borrower_status)
                   VALUES (%s, %s, %s, 'active') RETURNING borrower_id""",
                (uid, f"SEED100-{n:03d}", program),
            )
            borrower_ids.append((cur.fetchone()[0], is_faculty, program))

        # --- 2. pick books/accessions, keep tail unborrowed -----------------
        cur.execute(
            """SELECT a.accession_id, a.book_id FROM accession_log a
               JOIN book_catalog b ON a.book_id = b.book_id
               WHERE b.catalog_status = 'active' ORDER BY a.accession_id"""
        )
        copies = cur.fetchall()
        if len(copies) < 20:
            sys.exit(f"need >=20 accessions, found {len(copies)}")
        # Use all but the last 10 books' copies so underutilized stays non-empty.
        cur.execute(
            "SELECT book_id FROM book_catalog WHERE catalog_status='active' ORDER BY book_id"
        )
        all_books = [r[0] for r in cur.fetchall()]
        spare = set(all_books[-10:])
        pool = [c for c in copies if c[1] not in spare]
        if not pool:
            sys.exit("seed pool is empty — need active accessions outside the spare tail")
        # Weight a top-5 for "most borrowed / high demand" shape.
        top = pool[:5]
        if not top:
            sys.exit("seed pool too small to weight top titles")

        # --- 3. 100 circulation rows ----------------------------------------
        # Partial unique indexes (uq_active_loan_per_accession,
        # uq_active_loan_per_book_borrower) allow only one active/overdue
        # loan per copy and per (book, borrower): downgrade colliding picks
        # to returned rows.
        busy_accessions = set()
        busy_book_borrowers = set()
        inserted = 0
        for n in range(N_CIRCULATION):
            borrower_id, is_faculty, _prog = borrower_ids[n % len(borrower_ids)]
            # 40% of rows hit the top-5 books -> clear most-borrowed ranking.
            if rng.random() < 0.40:
                accession_id, book_id = rng.choice(top)
            else:
                accession_id, book_id = rng.choice(pool)
            days_ago = rng.randint(0, 179)
            borrow_date = today - timedelta(days=days_ago)
            overnight = rng.random() < 0.45
            borrow_type = "overnight" if overnight else "daily_circulation"
            loan_days = (30 if (overnight and is_faculty) else 2) if overnight else 0
            due_date = borrow_date + timedelta(days=loan_days)

            roll = rng.random()
            if roll < 0.60:
                status = "returned"
                return_date = borrow_date + timedelta(days=rng.randint(0, max(loan_days, 2)))
                lost = False
            elif roll < 0.85:
                status = "active"
                # keep active loans recent so they are plausibly still out
                if days_ago > 20:
                    borrow_date = today - timedelta(days=rng.randint(0, 20))
                    due_date = borrow_date + timedelta(days=loan_days)
                return_date = None
                lost = False
            else:
                status = "overdue"
                if days_ago < 10:
                    borrow_date = today - timedelta(days=rng.randint(10, 60))
                    due_date = borrow_date + timedelta(days=loan_days)
                return_date = None
                lost = rng.random() < 0.2
            if status in ("active", "overdue") and (
                accession_id in busy_accessions
                or (book_id, borrower_id) in busy_book_borrowers
            ):
                status = "returned"
                return_date = borrow_date + timedelta(days=rng.randint(0, max(loan_days, 2)))
                lost = False
            if status in ("active", "overdue"):
                busy_accessions.add(accession_id)
                busy_book_borrowers.add((book_id, borrower_id))
            cur.execute(
                """INSERT INTO circulation_records
                   (book_id, accession_id, borrower_id, processed_by, borrow_type,
                    transaction_type, borrow_date, due_date, return_date,
                    transaction_status, lost_flag)
                   VALUES (%s,%s,%s,%s,%s,'borrow',%s,%s,%s,%s,%s)""",
                (
                    book_id, accession_id, borrower_id, processed_by, borrow_type,
                    borrow_date, due_date, return_date, status, lost,
                ),
            )
            inserted += 1

        # --- 4. inventory top-up for condition chart -------------------------
        cur.execute(
            """SELECT a.accession_id FROM accession_log a
               LEFT JOIN inventory_status i ON i.accession_id = a.accession_id
               WHERE i.inventory_id IS NULL ORDER BY a.accession_id LIMIT 30"""
        )
        missing = [r[0] for r in cur.fetchall()]
        states = (
            ["available"] * 16 + ["borrowed"] * 8
            + ["damaged"] * 2 + ["missing"] * 2 + ["lost"] * 2
        )
        for k, acc_id in enumerate(missing):
            state = states[k % len(states)]
            cur.execute(
                """INSERT INTO inventory_status
                   (accession_id, inventory_state, inventory_type, checked_by,
                    last_checked_date, notes)
                   VALUES (%s,%s,'realtime_scan',%s,%s,'SEED100')""",
                (acc_id, state, processed_by, today),
            )

        conn.commit()
        print(f"seeded {len(borrower_ids)} borrowers + {inserted} circulation rows")
        print(f"inventory topped up for {len(missing)} accessions")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed 100 analytics circulation rows.")
    parser.add_argument(
        "--reset",
        dest="reset",
        action="store_true",
        default=True,
        help="Delete prior SEED100 rows before seeding (default).",
    )
    parser.add_argument(
        "--no-reset",
        dest="reset",
        action="store_false",
        help="Append seed rows without cleaning prior SEED100 rows.",
    )
    args = parser.parse_args()
    main(reset=args.reset)
