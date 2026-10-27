import os
import psycopg2
from dotenv import load_dotenv

def run_seed():
    load_dotenv('.env')
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not found in .env")
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        print("Starting realistic data update...")

        # 1. Update user_accounts (names and emails)
        users_to_update = [
            (60, "Patricia Anne Reyes", "patricia.reyes@mcst.edu.ph"),
            (61, "Marco Luis Villanueva", "marco.villanueva@mcst.edu.ph"),
            (62, "Sophia Mae dela Cruz", "sophia.delacruz@mcst.edu.ph"),
            (63, "Reinaldo B. Ocampo", "reinaldo.ocampo@mcst.edu.ph"),
            (64, "Cecilia M. Navarro", "cecilia.navarro@mcst.edu.ph"),
            (65, "Rosario C. Castillo", "rosario.castillo@mcst.edu.ph"),
            (66, "Emmanuel P. Torres", "emmanuel.torres@mcst.edu.ph"),
            (67, "Alex Santos", "alex.santos@mcst.edu.ph"),
            (68, "Maria Bautista", "maria.bautista@mcst.edu.ph"),
            (69, "Jose Mendoza", "jose.mendoza@mcst.edu.ph"),
            (70, "Ana Aquino", "ana.aquino@mcst.edu.ph"),
            (71, "Mark de Leon", "mark.deleon@mcst.edu.ph"),
            (72, "Liza Ramos", "liza.ramos@mcst.edu.ph"),
            (73, "John Villanueva", "john.villanueva@mcst.edu.ph"),
            (74, "Rosa Garcia", "rosa.garcia@mcst.edu.ph"),
            (75, "Paolo Fernandez", "paolo.fernandez@mcst.edu.ph"),
            (76, "Nina Coronel", "nina.coronel@mcst.edu.ph"),
            (77, "Carlos dela Rosa", "carlos.delarosa@mcst.edu.ph"),
            (78, "Ella Marasigan", "ella.marasigan@mcst.edu.ph"),
            (79, "Alma Punzalan", "alma.punzalan@mcst.edu.ph"),
            (80, "Diego Manalo", "diego.manalo@mcst.edu.ph"),
            (81, "Paula Sta. Maria", "paula.stamaria@mcst.edu.ph"),
            (82, "Andrew Dimaculangan", "andrew.dimaculangan@mcst.edu.ph"),
        ]

        for uid, name, email in users_to_update:
            cur.execute("""
                UPDATE user_accounts
                SET full_name = %s, email = %s
                WHERE user_id = %s
            """, (name, email, uid))
        print(f"Updated {len(users_to_update)} user accounts.")

        # 2. Update borrowers table (id_number, department, phone_number)
        borrowers_to_update = [
            (60, "2023-1045", "BS Information Systems", "+63 917 123 4567"),
            (61, "2023-1102", "BS Nursing", "+63 918 234 5678"),
            (62, "2024-0518", "Bachelor of Arts in Communication", "+63 919 345 6789"),
            (63, "FAC-2018-042", "BS Information Systems", "+63 920 456 7890"),
            (64, "FAC-2019-015", "BS Nursing", "+63 921 567 8901"),
            (65, "LIB-2020-003", "Library Department", "+63 922 678 9012"),
            (66, "ADM-2017-001", "Information Technology Office", "+63 923 789 0123"),
            (67, "2022-0194", "BS Information Systems", "+63 924 890 1234"),
            (68, "2022-0341", "BS Nursing", "+63 925 901 2345"),
            (69, "2023-0872", "Bachelor of Arts in Communication", "+63 926 012 3456"),
            (70, "2023-0459", "BS Business Administration", "+63 927 123 4567"),
            (71, "2024-0112", "BS Information Systems", "+63 928 234 5678"),
            (72, "2024-0238", "BS Nursing", "+63 929 345 6789"),
            (73, "2023-0661", "Bachelor of Arts in Communication", "+63 930 456 7890"),
            (74, "2022-0582", "BS Hospitality Management", "+63 931 567 8901"),
            (75, "2023-0914", "BS Information Systems", "+63 932 678 9012"),
            (76, "2024-0429", "BS Nursing", "+63 933 789 0123"),
            (77, "2022-0731", "Bachelor of Arts in Communication", "+63 934 890 1234"),
            (78, "2023-0185", "BS Tourism Management", "+63 935 901 2345"),
            (79, "2021-0089", "BS Information Systems", "+63 936 012 3456"),
            (80, "2021-0412", "BS Business Administration", "+63 937 123 4567"),
            (81, "2024-0890", "Bachelor of Arts in Communication", "+63 938 234 5678"),
            (82, "2024-0995", "BS Nursing", "+63 939 345 6789"),
        ]

        for uid, id_num, dept, phone in borrowers_to_update:
            cur.execute("""
                UPDATE borrowers
                SET id_number = %s, department = %s, phone_number = %s
                WHERE user_id = %s
            """, (id_num, dept, phone, uid))
        print("Updated borrower records.")

        # 3. Update book_catalog (replace demo books 411, 412, 413)
        books_to_update = [
            (
                411,
                "Introduction to Information Systems",
                "R. Kelly Rainer, Patrick Wang, Mary Anne Rajkumar",
                "John Wiley & Sons",
                2021,
                "978-1-119-80148-5",
                "Technology & Computing",
                "Information systems fundamentals covering IT architecture, digital business, analytics, and organizational impact."
            ),
            (
                412,
                "Database System Concepts",
                "Abraham Silberschatz, Henry F. Korth, S. Sudarshan",
                "McGraw-Hill Education",
                2020,
                "978-0-07-802215-9",
                "Technology & Computing",
                "Comprehensive textbook on relational database design, query optimization, transaction processing, and modern storage architectures."
            ),
            (
                413,
                "Web Development and Design Foundations with HTML5",
                "Terry Felke-Morris",
                "Pearson Education",
                2019,
                "978-0-13-470927-8",
                "Technology & Computing",
                "Hands-on guide to responsive web design, modern HTML5 semantic markup, CSS Grid, Flexbox, and user accessibility standards."
            )
        ]

        for bid, title, author, pub, yr, isbn, cat, desc in books_to_update:
            cur.execute("""
                UPDATE book_catalog
                SET title = %s, author = %s, publisher = %s, year_published = %s,
                    isbn = %s, subject_classification = %s, description = %s, catalog_status = 'active'
                WHERE book_id = %s
            """, (title, author, pub, yr, isbn, cat, desc, bid))
        print("Updated book_catalog for books 411-413.")

        # 4. Update accession numbers for copies of 411, 412, 413
        cur.execute("SELECT accession_id, book_id FROM accession_log WHERE book_id IN (411, 412, 413) ORDER BY accession_id")
        copies = cur.fetchall()
        for acc_id, b_id in copies:
            new_acc_num = f"2024-{acc_id:05d}"
            cur.execute("UPDATE accession_log SET accession_number = %s WHERE accession_id = %s", (new_acc_num, acc_id))
        print(f"Updated accession numbers for {len(copies)} copies.")

        # 5. Fix overdue circulation records
        cur.execute("""
            UPDATE circulation_records
            SET transaction_status = 'overdue',
                fine_amount = GREATEST(5.00, (DATE '2026-10-13' - due_date::date) * 5.00)
            WHERE transaction_status = 'active'
              AND due_date::date < DATE '2026-10-13'
        """)
        print(f"Marked {cur.rowcount} overdue loans.")

        # 6. Notifications: refresh with realistic notification messages
        cur.execute("DELETE FROM notification_log")
        notifications = [
            (60, "You have borrowed 'Web Development and Design Foundations with HTML5'. Due on Oct 27, 2026.", "borrow", "CIRC-1045", False, "2026-10-12 14:30:00"),
            (60, "Your reserved copy of 'Database System Concepts' is ready for claim at the circulation desk until Oct 15, 2026.", "hold_ready", "RES-412", False, "2026-10-12 16:00:00"),
            (60, "Your procurement request for 'Clean Code: A Handbook of Agile Software Craftsmanship' has been approved by the library committee.", "request_update", "REQ-88", True, "2026-10-11 09:15:00"),
            (61, "Reminder: Your borrowed book 'Essentials of Psychiatric Mental Health Nursing' is due tomorrow, Oct 14, 2026.", "due_soon", "CIRC-1102", False, "2026-10-12 08:00:00"),
            (62, "Notice: 'Media and Culture: An Introduction to Mass Communication' was due on Oct 08, 2026. Please return promptly to settle accrued fines.", "overdue_reminder", "CIRC-0518", False, "2026-10-11 10:20:00"),
            (63, "Your faculty book request for 'Deep Learning with Python' has been ordered from the publisher.", "request_update", "REQ-92", True, "2026-10-10 11:45:00"),
            (64, "Return confirmed for 'Medical-Surgical Nursing: Concepts for Clinical Judgment'. Thank you for returning on time.", "return", "CIRC-0915", True, "2026-10-09 15:20:00"),
            (67, "Reminder: 'Operating System Concepts' is due on Oct 16, 2026.", "due_soon", "CIRC-0194", False, "2026-10-12 11:10:00"),
            (68, "Your reservation for 'Pharmacology and the Nursing Process' was successfully claimed.", "reservation", "RES-341", True, "2026-10-08 14:05:00"),
            (69, "Your book recommendation has been submitted to the acquisition librarian for evaluation.", "request_update", "REQ-72", True, "2026-10-07 13:30:00"),
            (70, "Your MCST Library student borrowing account is fully active for Academic Year 2026-2027.", "status_update", "USR-70", True, "2026-10-01 08:30:00"),
            (71, "Notice: 'Artificial Intelligence: A Modern Approach' is overdue. Current fine: ₱25.00.", "fine", "CIRC-0112", False, "2026-10-12 10:00:00"),
            (72, "A requested copy of 'Maternal and Child Health Nursing' has been reserved under your account.", "reservation", "RES-238", False, "2026-10-12 15:50:00"),
        ]

        # Map user_id to borrower_id
        cur.execute("SELECT user_id, borrower_id FROM borrowers")
        u2b = dict(cur.fetchall())

        for uid, msg, n_type, ref, is_read, date_sent in notifications:
            bid = u2b.get(uid)
            if bid:
                cur.execute("""
                    INSERT INTO notification_log (recipient_id, message, notif_type, related_reference, is_read, date_sent)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (bid, msg, n_type, ref, is_read, date_sent))
        print("Refreshed notification log.")

        # 7. Audit trail: ensure clean, realistic records
        cur.execute("UPDATE audit_trail SET activity = REPLACE(activity, 'Demo Librarian', 'Rosario C. Castillo') WHERE activity LIKE '%Demo Librarian%'")
        cur.execute("UPDATE audit_trail SET activity = REPLACE(activity, 'Demo Admin', 'Emmanuel P. Torres') WHERE activity LIKE '%Demo Admin%'")
        cur.execute("UPDATE audit_trail SET activity = REPLACE(activity, 'Demo Student', 'Patricia Anne Reyes') WHERE activity LIKE '%Demo Student%'")

        extra_audits = [
            (65, "cataloging:create_book:413", "sess_lib_01", "2026-10-10 09:30:15"),
            (65, "circulation:checkout:1045", "sess_lib_01", "2026-10-10 10:14:22"),
            (65, "circulation:checkin:1012", "sess_lib_01", "2026-10-11 11:05:40"),
            (66, "admin:role_change:63", "sess_adm_01", "2026-10-09 14:20:00"),
            (66, "backup:manual_create:success", "sess_adm_01", "2026-10-10 03:00:10"),
            (65, "inventory:audit_shelf:CS-01", "sess_lib_01", "2026-10-11 16:45:00"),
            (65, "requests:approve:48", "sess_lib_01", "2026-10-11 13:10:00"),
            (66, "settings:update:circulation_policy", "sess_adm_01", "2026-10-08 15:30:00"),
        ]
        for uid, act, sess, ts in extra_audits:
            cur.execute("""
                INSERT INTO audit_trail (user_id, activity, session_token, log_timestamp)
                VALUES (%s, %s, %s, %s)
            """, (uid, act, sess, ts))
        print("Updated audit trail.")

        # 8. Backup logs: insert realistic history if needed
        cur.execute("SELECT count(*) FROM backup_log")
        bcount = cur.fetchone()[0]
        if bcount < 5:
            extra_backups = [
                ("mcst_lms_backup_20261010_030000.sql.gz", 14820512, "completed", "scheduled", None, "2026-10-10 03:00:00"),
                ("mcst_lms_backup_20261005_120000.sql.gz", 14751024, "completed", "manual", None, "2026-10-05 12:00:00"),
                ("mcst_lms_backup_20260930_030000.sql.gz", 14619420, "completed", "scheduled", None, "2026-09-30 03:00:00"),
                ("mcst_lms_backup_20260920_030000.sql.gz", 14502800, "completed", "scheduled", None, "2026-09-20 03:00:00"),
                ("mcst_lms_backup_20260910_154500.sql.gz", 14389100, "completed", "manual", None, "2026-09-10 15:45:00"),
            ]
            for filename, size, status, b_type, err, created_at in extra_backups:
                cur.execute("""
                    INSERT INTO backup_log (filename, size_bytes, status, backup_type, error_msg, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (filename, size, status, b_type, err, created_at))
            print("Added backup logs.")

        conn.commit()
        print("SUCCESS: Realistic database seed completed and committed.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Seeding failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_seed()
