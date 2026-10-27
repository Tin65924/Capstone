"""Supplemental demo seeder — fills every table the other seeders skip.

Usage:
    venv\\Scripts\\python.exe dev/seed_demo_supplement.py [--reset | --no-reset]

What it does (tag SEEDSUP, rerunnable, single transaction):
    1. Account variety: 1 archived user, 1 disabled user (blocked borrower),
       1 pending Faculty (+ borrower) so every Users-page card has data.
    2. 1 archived book (no active loans) for the Archived catalog tab.
    3. Approves 5 pending requests, then writes 6 procurement_log rows across
       ALL order statuses (for_ordering/ordered/delivered/procured/
       cancelled+remarks/out_of_stock).
    4. reservation_queue rows in waiting/allocated/claimed/expired states.
    5. notification_log rows of every type used by the app.
    6. user_favorites for a few users.
    7. Overdue fines (2 unpaid, 1 paid) on existing overdue loans.
    8. inventory_sessions (1 active + 1 completed) + fresh condition rows.
    9. audit_trail rows so the activity feed is non-empty.
"""

import argparse
import os
import sys
from datetime import date, timedelta

SEED_TAG = "SEEDSUP"
SEED_DOMAIN = "mcst.edu.ph"

SUP_USERS = [
    # (email_prefix, full_name, role, account_status, id_number, department, borrower_status)
    ("seedsup_archived", "Archived Alma", "Student", "archived", "SEEDSUP-001", "BSIS", "active"),
    ("seedsup_disabled", "Disabled Diego", "Student", "disabled", "SEEDSUP-002", "BSN", "blocked"),
    ("seedsup_pendingfac", "Pending Paula", "Faculty", "pending", "SEEDSUP-003", "BS Information Systems", "active"),
    ("seedsup_active", "Active Andy", "Student", "active", "SEEDSUP-004", "BS Criminology", "active"),
]


def get_conn():
    from dotenv import load_dotenv

    load_dotenv()
    import psycopg2

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        sys.exit("DATABASE_URL not set in .env (run setup_db.py first)")
    return psycopg2.connect(dsn)


def reset_seed(cur):
    id_pattern = SEED_TAG + "-%"
    email_pattern = SEED_TAG.lower() + "!_%%@%s" % SEED_DOMAIN
    cur.execute("SELECT borrower_id FROM borrowers WHERE id_number LIKE %s", (id_pattern,))
    bids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT user_id FROM user_accounts WHERE email LIKE %s ESCAPE '!'", (email_pattern,))
    uids = [r[0] for r in cur.fetchall()]
    if bids:
        cur.execute("DELETE FROM reservation_queue WHERE borrower_id = ANY(%s)", (bids,))
        cur.execute("DELETE FROM notification_log WHERE recipient_id = ANY(%s)", (bids,))
        cur.execute("DELETE FROM circulation_records WHERE borrower_id = ANY(%s)", (bids,))
    cur.execute("DELETE FROM notification_log WHERE message LIKE %s", ("[" + SEED_TAG + "]%",))
    cur.execute("DELETE FROM audit_trail WHERE activity LIKE %s", ("[" + SEED_TAG + "]%",))
    cur.execute("DELETE FROM inventory_status WHERE notes = %s", (SEED_TAG,))
    if uids:
        cur.execute("DELETE FROM user_favorites WHERE user_id = ANY(%s)", (uids,))
        cur.execute("DELETE FROM audit_trail WHERE user_id = ANY(%s)", (uids,))
    cur.execute("DELETE FROM borrowers WHERE id_number LIKE %s", (id_pattern,))
    cur.execute("DELETE FROM user_accounts WHERE email LIKE %s ESCAPE '!'", (email_pattern,))
    cur.execute("UPDATE book_catalog SET catalog_status = 'active' WHERE book_id IN "
                "(SELECT book_id FROM book_catalog WHERE description LIKE %s)", ("%[" + SEED_TAG + "]%",))
    print("prior SEEDSUP rows cleared")


def main(reset=True):
    today = date.today()
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        if reset:
            reset_seed(cur)

        cur.execute("SELECT role_id, role_name FROM roles")
        roles = {name: rid for rid, name in cur.fetchall()}

        cur.execute("SELECT user_id FROM user_accounts ORDER BY user_id LIMIT 1")
        row = cur.fetchone()
        if not row:
            sys.exit("no users in DB — run seed_books.py first")
        processed_by = row[0]

        # --- 1. account variety -------------------------------------------
        borrower_ids = {}
        for prefix, full_name, role, status, id_number, dept, bstatus in SUP_USERS:
            cur.execute(
                """INSERT INTO user_accounts (email, oauth_sub, full_name, role_id, account_status)
                   VALUES (%s, %s, %s, %s, %s) RETURNING user_id""",
                (f"{prefix}@{SEED_DOMAIN}", f"{SEED_TAG.lower()}_oauth_{prefix}",
                 full_name, roles[role], status),
            )
            uid = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO borrowers (user_id, id_number, department, borrower_status)
                   VALUES (%s, %s, %s, %s) RETURNING borrower_id""",
                (uid, id_number, dept, bstatus),
            )
            borrower_ids[prefix] = cur.fetchone()[0]
        print(f"seeded {len(SUP_USERS)} account-variety users")

        # --- 2. one archived book (no active loans on it) ------------------
        cur.execute(
            """SELECT b.book_id FROM book_catalog b
               WHERE b.catalog_status = 'active'
               AND NOT EXISTS (SELECT 1 FROM circulation_records c
                               WHERE c.book_id = b.book_id
                               AND c.transaction_status IN ('active', 'overdue'))
               ORDER BY b.book_id DESC LIMIT 1"""
        )
        arch_book = cur.fetchone()[0]
        cur.execute(
            "UPDATE book_catalog SET catalog_status = 'archived', description = COALESCE(description, '') || %s "
            "WHERE book_id = %s",
            (f" [{SEED_TAG}]", arch_book),
        )
        print(f"archived book_id={arch_book}")

        # --- 3. procurement across all statuses ----------------------------
        cur.execute(
            "SELECT request_id FROM request_records WHERE request_status = 'approved' ORDER BY request_id"
        )
        approved = [r[0] for r in cur.fetchall()]
        cur.execute(
            "SELECT request_id FROM request_records WHERE request_status = 'pending_review' "
            "ORDER BY request_id LIMIT %s", (6 - len(approved),)
        )
        to_approve = [r[0] for r in cur.fetchall()]
        for rid in to_approve:
            cur.execute(
                "UPDATE request_records SET request_status = 'approved', reviewed_by = %s, "
                "review_date = NOW() WHERE request_id = %s",
                (processed_by, rid),
            )
        approved += to_approve
        cur.execute("SELECT book_id FROM book_catalog WHERE catalog_status = 'active' ORDER BY book_id LIMIT 1")
        sample_book = cur.fetchone()[0]
        statuses = [
            ("for_ordering", None, None, None),
            ("ordered", "PO-2026-001 sent to supplier", None, None),
            ("delivered", "Arrived at receiving", today - timedelta(days=2), None),
            ("procured", "Cataloged", today - timedelta(days=1), sample_book),
            ("cancelled", "Out of budget this term", None, None),
            ("out_of_stock", "Supplier has no stock", None, None),
        ]
        for rid, (ostatus, remarks, received, book_id) in zip(approved, statuses):
            cur.execute(
                """INSERT INTO procurement_log (request_id, order_status, order_date,
                                              date_received, book_id, remarks)
                   SELECT %s, %s, %s, %s, %s, %s
                   WHERE NOT EXISTS (SELECT 1 FROM procurement_log WHERE request_id = %s)""",
                (rid, ostatus, today - timedelta(days=10), received, book_id, remarks, rid),
            )
        print(f"seeded {min(len(approved), 6)} procurement rows")

        # --- 4. reservations in every state --------------------------------
        # One borrower (SEEDSUP active) x 4 books keeps reset simple and
        # respects the active-reservation unique indexes.
        res_borrower = borrower_ids["seedsup_active"]
        cur.execute("SELECT DISTINCT book_id FROM accession_log ORDER BY book_id LIMIT 4")
        res_books = [r[0] for r in cur.fetchall()]
        res_states = ["waiting", "allocated", "claimed", "expired"]
        n_res = 0
        for book_id, state in zip(res_books, res_states):
            cur.execute(
                "SELECT 1 FROM reservation_queue WHERE book_id = %s AND borrower_id = %s",
                (book_id, res_borrower),
            )
            if cur.fetchone():
                continue
            cur.execute(
                "SELECT COALESCE(MAX(queue_position), 0) + 1 FROM reservation_queue WHERE book_id = %s",
                (book_id,),
            )
            pos = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO reservation_queue (book_id, borrower_id, queue_position,
                                               reservation_status)
                   VALUES (%s, %s, %s, %s)""",
                (book_id, res_borrower, pos, state),
            )
            n_res += 1
        print(f"seeded {n_res} reservation rows")

        # --- 5. notifications of every type ---------------------------------
        cur.execute(
            "SELECT borrower_id FROM borrowers WHERE borrower_status = 'active' ORDER BY borrower_id LIMIT 4"
        )
        res_borrowers = [r[0] for r in cur.fetchall()]
        notifs = [
            ("request_update", "Your book request was approved."),
            ("overdue_reminder", "Overdue: please return your book to avoid further fines."),
            ("hold_ready", "A reserved copy is ready for pickup."),
            ("borrow", "You borrowed a book. Due soon."),
            ("return", "You returned your book. Thank you!"),
            ("fine", "Overdue fine assessed. Please settle at the desk."),
            ("due_soon", "Reminder: your book is due in 2 days."),
            ("reservation", "Reservation placed. You will be notified when ready."),
            ("status_update", "Your account status was updated."),
        ]
        for i, (ntype, msg) in enumerate(notifs):
            cur.execute(
                """INSERT INTO notification_log (recipient_id, message, notif_type, related_reference)
                   VALUES (%s, %s, %s, %s)""",
                (res_borrowers[i % len(res_borrowers)], f"[{SEED_TAG}] {msg}", ntype, str(i + 1)),
            )
        print(f"seeded {len(notifs)} notification rows")

        # --- 6. favorites ----------------------------------------------------
        cur.execute("SELECT user_id FROM user_accounts ORDER BY user_id LIMIT 2")
        fav_users = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT book_id FROM book_catalog WHERE catalog_status = 'active' ORDER BY book_id LIMIT 4")
        fav_books = [r[0] for r in cur.fetchall()]
        for uid, bid in zip(fav_users * 2, fav_books):
            cur.execute(
                "INSERT INTO user_favorites (user_id, book_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (uid, bid),
            )
        print("seeded favorites")

        # --- 7. overdue fines (2 unpaid, 1 paid) ------------------------------
        cur.execute(
            "SELECT circulation_id FROM circulation_records "
            "WHERE transaction_status = 'overdue' ORDER BY circulation_id LIMIT 3"
        )
        overdue_ids = [r[0] for r in cur.fetchall()]
        for j, cid in enumerate(overdue_ids):
            cur.execute(
                "UPDATE circulation_records SET fine_amount = %s, fine_paid = %s WHERE circulation_id = %s",
                (25.00 * (j + 1), j == 2, cid),
            )
        print(f"set fines on {len(overdue_ids)} overdue loans")

        # --- 8. inventory sessions + condition rows ---------------------------
        # Reuse existing sessions on reruns (no owner tag column to match on).
        cur.execute("SELECT session_id FROM inventory_sessions WHERE session_status = 'active' ORDER BY session_id LIMIT 1")
        row = cur.fetchone()
        if row:
            active_session = row[0]
        else:
            cur.execute(
                """INSERT INTO inventory_sessions (librarian_id, total_books, scanned_count, session_status)
                   VALUES (%s, %s, %s, 'active') RETURNING session_id""",
                (processed_by, 100, 12),
            )
            active_session = cur.fetchone()[0]
        cur.execute("SELECT session_id FROM inventory_sessions WHERE session_status = 'completed' ORDER BY session_id LIMIT 1")
        row = cur.fetchone()
        if not row:
            cur.execute(
                """INSERT INTO inventory_sessions (librarian_id, total_books, scanned_count,
                                                  session_status, ended_at)
                   VALUES (%s, %s, %s, 'completed', NOW()) RETURNING session_id""",
                (processed_by, 100, 100),
            )
        done_session = (row[0] if row else cur.fetchone()[0])
        cur.execute(
            """SELECT a.accession_id FROM accession_log a
               LEFT JOIN inventory_status i ON i.accession_id = a.accession_id
               WHERE i.inventory_id IS NULL ORDER BY a.accession_id LIMIT 4"""
        )
        fresh = [r[0] for r in cur.fetchall()]
        for acc_id, state in zip(fresh, ["lost", "damaged", "missing", "available"]):
            cur.execute(
                """INSERT INTO inventory_status (accession_id, inventory_state, inventory_type,
                                               checked_by, last_checked_date, session_id, notes)
                   VALUES (%s, %s, 'annual_physical', %s, %s, %s, %s)""",
                (acc_id, state, processed_by, today, active_session, SEED_TAG),
            )
        print(f"seeded 2 inventory sessions + {len(fresh)} condition rows")

        # --- 9. audit trail ----------------------------------------------------
        for uid in fav_users:
            for activity in ("login", "cataloging:export_books:all:10"):
                cur.execute(
                    "INSERT INTO audit_trail (user_id, activity) VALUES (%s, %s)",
                    (uid, f"[{SEED_TAG}] {activity}"),
                )
        print("seeded audit rows")

        conn.commit()
        print("supplement seed complete")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed leftover demo tables.")
    parser.add_argument("--reset", dest="reset", action="store_true", default=True)
    parser.add_argument("--no-reset", dest="reset", action="store_false")
    args = parser.parse_args()
    main(reset=args.reset)
