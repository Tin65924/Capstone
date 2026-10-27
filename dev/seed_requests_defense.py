"""Seed defense-ready Book Request demo data (Student vs Faculty stacked demand).

Usage:
    venv\\Scripts\\python.exe dev/seed_requests_defense.py [--reset | --no-reset]

What it does:
    1. Ensures the 4 roles exist (Student, Faculty, Librarian, Admin).
    2. Creates 7 demo users covering ALL roles (tag SEEDREQ):
         - 3 Students, 2 Faculty (+ borrowers), 1 Librarian, 1 Admin
         - emails: seedreq_student1@mcst.edu.ph, ... (all @mcst.edu.ph so
           they match the Google OAuth domain rule).
    3. Inserts request_records for books NOT in the library, shaped so the
       new stacked-bar overview has something to show:
         - "Introduction to Data Science" — 3 students + 2 faculty
         - "Philippine History: A New Narrative" — 2 students + 1 faculty
         - "Clean Architecture in Practice" — 2 students only
         - "Advanced Research Methods" — 1 faculty only
         - "Creative Writing for Beginners" — 1 student + 1 faculty (approved)
       All other rows stay 'pending_review' so Approve/Reject can be
       demoed live during the defense.

    4. For ACTUAL book data (adviser asked for real books, not mock):
       import books_seed.csv / books_copies_extra.csv via the Cataloging
       bulk-import page — this seeder intentionally does NOT fake the
       catalog. It only seeds users + requests.

Rerunnable: with --reset (default) prior SEEDREQ requests/borrowers/users
are deleted first. Pass --no-reset to append.
"""
import argparse
import os
import sys

SEED_TAG = "SEEDREQ"
SEED_DOMAIN = "mcst.edu.ph"

DEMO_USERS = [
    # (email_prefix, full_name, role, id_number, department)
    ("seedreq_student1", "Demo Student One", "Student", "SEEDREQ-001", "BSIS"),
    ("seedreq_student2", "Demo Student Two", "Student", "SEEDREQ-002", "BSN"),
    ("seedreq_student3", "Demo Student Three", "Student", "SEEDREQ-003", "BACOMM"),
    ("seedreq_faculty1", "Demo Faculty One", "Faculty", "SEEDREQ-101", "Computing"),
    ("seedreq_faculty2", "Demo Faculty Two", "Faculty", "SEEDREQ-102", "Nursing"),
    ("seedreq_librarian1", "Demo Librarian", "Librarian", None, None),
    ("seedreq_admin1", "Demo Admin", "Admin", None, None),
]

# (title, author, student_idxs, faculty_idxs, status)
# idxs refer to positions within the student / faculty demo lists above.
DEMO_REQUESTS = [
    ("Introduction to Data Science", "Joel Grus", [0, 1, 2], [0, 1], "pending_review"),
    ("Philippine History: A New Narrative", "Maria Santos", [0, 1], [0], "pending_review"),
    ("Clean Architecture in Practice", "Robert C. Martin", [1, 2], [], "pending_review"),
    ("Advanced Research Methods", "John Creswell", [], [1], "pending_review"),
    ("Creative Writing for Beginners", "Ana Reyes", [2], [0], "approved"),
]


def get_conn():
    """Open a psycopg2 connection from ``DATABASE_URL`` in ``.env``.

    Loads ``.env`` and connects with the ``DATABASE_URL`` value; exits
    the process with a message when it is unset (hinting at
    ``setup_db.py``), since the request seeder cannot run offline.

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
        sys.exit("DATABASE_URL not set in .env (run setup_db.py first)")
    return psycopg2.connect(dsn)


def reset_seed(cur):
    """Delete prior SEEDREQ request-demo rows in dependency order.

    Removes procurement/notification/request rows for ``SEEDREQ-*``
    borrowers and audit rows for ``seedreq_*`` users, then the
    borrowers and users themselves, so a rerun starts clean. Only
    ``SEEDREQ``-tagged rows match; the real catalog is untouched.

    Args:
        cur: Open DB cursor on the seeding transaction.

    Returns:
        None.

    Side effects:
        DELETEs prior SEEDREQ rows across 6 tables; prints per-table
        row counts.
    """
    id_pattern = SEED_TAG + "-%"
    email_pattern = SEED_TAG.lower() + "!_%%@%s" % SEED_DOMAIN
    cur.execute("SELECT borrower_id FROM borrowers WHERE id_number LIKE %s", (id_pattern,))
    bids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT user_id FROM user_accounts WHERE email LIKE %s ESCAPE '!'", (email_pattern,))
    uids = [r[0] for r in cur.fetchall()]
    if bids:
        cur.execute("DELETE FROM procurement_log WHERE request_id IN "
                    "(SELECT request_id FROM request_records WHERE requester_id = ANY(%s))", (bids,))
        print(f"removed {cur.rowcount} prior {SEED_TAG} procurement rows")
        cur.execute("DELETE FROM notification_log WHERE recipient_id = ANY(%s)", (bids,))
        print(f"removed {cur.rowcount} prior {SEED_TAG} notification rows")
        cur.execute("DELETE FROM request_records WHERE requester_id = ANY(%s)", (bids,))
        print(f"removed {cur.rowcount} prior {SEED_TAG} request rows")
    if uids:
        cur.execute("DELETE FROM user_favorites WHERE user_id = ANY(%s)", (uids,))
        print(f"removed {cur.rowcount} prior {SEED_TAG} favorite rows")
        cur.execute("DELETE FROM audit_trail WHERE user_id = ANY(%s)", (uids,))
        print(f"removed {cur.rowcount} prior {SEED_TAG} audit rows")
    cur.execute("DELETE FROM borrowers WHERE id_number LIKE %s", (id_pattern,))
    print(f"removed {cur.rowcount} prior {SEED_TAG} borrowers")
    cur.execute("DELETE FROM user_accounts WHERE email LIKE %s ESCAPE '!'", (email_pattern,))
    print(f"removed {cur.rowcount} prior {SEED_TAG} users")


def main(reset=True):
    """Seed 7 demo users and stacked-demand book requests for defense.

    Ensures all 4 roles exist, creates 3 Students + 2 Faculty (with
    borrowers) + 1 Librarian + 1 Admin (``SEEDREQ``/``seedreq_*``), then
    inserts ``DEMO_REQUESTS`` shaped for the stacked-bar overview (one
    title with both student+faculty demand, student-only, faculty-only
    and one pre-approved row; the rest stay ``pending_review`` for a
    live approve/reject demo). Commits on success, rolls back on error.

    Args:
        reset (bool): When True (default), delete prior SEEDREQ rows
            first; pass False (``--no-reset``) to append.

    Returns:
        None.

    Side effects:
        INSERTs roles, users, borrowers and request rows; commits on
        success, rolls back on failure; prints seed/next-step summary.
    """
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        if reset:
            reset_seed(cur)

        cur.execute("SELECT role_id, role_name FROM roles")
        roles = {name: rid for rid, name in cur.fetchall()}
        for needed in ("Student", "Faculty", "Librarian", "Admin"):
            if needed not in roles:
                cur.execute("INSERT INTO roles (role_name) VALUES (%s) RETURNING role_id", (needed,))
                roles[needed] = cur.fetchone()[0]

        cur.execute("SELECT user_id FROM user_accounts ORDER BY user_id LIMIT 1")
        row = cur.fetchone()
        reviewer_id = row[0] if row else None

        # --- 1. demo users + borrowers (all 4 roles present) ---------------
        student_borrowers = []
        faculty_borrowers = []
        for prefix, full_name, role, id_number, dept in DEMO_USERS:
            email = f"{prefix}@{SEED_DOMAIN}"
            cur.execute(
                """INSERT INTO user_accounts (email, oauth_sub, full_name, role_id, account_status)
                   VALUES (%s, %s, %s, %s, 'active') RETURNING user_id""",
                (email, f"{SEED_TAG.lower()}_oauth_{prefix}", full_name, roles[role]),
            )
            uid = cur.fetchone()[0]
            if id_number:
                cur.execute(
                    """INSERT INTO borrowers (user_id, id_number, department, borrower_status)
                       VALUES (%s, %s, %s, 'active') RETURNING borrower_id""",
                    (uid, id_number, dept),
                )
                bid = cur.fetchone()[0]
                if role == "Student":
                    student_borrowers.append(bid)
                elif role == "Faculty":
                    faculty_borrowers.append(bid)

        # --- 2. book requests (books NOT in library) ------------------------
        for title, author, s_idxs, f_idxs, status in DEMO_REQUESTS:
            targets = [student_borrowers[i] for i in s_idxs] + [faculty_borrowers[i] for i in f_idxs]
            for bid in targets:
                if status == "approved" and reviewer_id:
                    cur.execute(
                        """INSERT INTO request_records
                           (requester_id, book_title, author, request_status, reviewed_by, review_date)
                           VALUES (%s, %s, %s, 'approved', %s, NOW())""",
                        (bid, title, author, reviewer_id),
                    )
                else:
                    cur.execute(
                        """INSERT INTO request_records (requester_id, book_title, author, request_status)
                           VALUES (%s, %s, %s, 'pending_review')""",
                        (bid, title, author),
                    )

        cur.execute("SELECT COUNT(*) FROM request_records WHERE requester_id = ANY(%s)",
                    (student_borrowers + faculty_borrowers,))
        total = cur.fetchone()[0]

        conn.commit()
        print(f"seeded {len(DEMO_USERS)} demo users (3 Student + 2 Faculty + 1 Librarian + 1 Admin)")
        print(f"seeded {len(student_borrowers) + len(faculty_borrowers)} borrowers + {total} book requests")
        print("Top demo bar: 'Introduction to Data Science' = 3 students + 2 faculty (both sides).")
        print("Next step for ACTUAL data: Cataloging > Bulk Import > upload books_seed.csv")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed defense book-request demo data.")
    parser.add_argument("--reset", dest="reset", action="store_true", default=True,
                        help="Delete prior SEEDREQ rows before seeding (default).")
    parser.add_argument("--no-reset", dest="reset", action="store_false",
                        help="Append seed rows without cleaning prior SEEDREQ rows.")
    args = parser.parse_args()
    main(reset=args.reset)
