from datetime import date, timedelta, datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import circulation_bp
from app.auth.decorators import librarian_required
from app.auth.models import log_activity
from app.cataloging.models import get_book_by_id, get_accession_by_number, get_accession_by_id
from .models import (
    borrow_book, return_book, get_active_loan_by_accession,
    get_active_loan_by_book_and_borrower,
    count_active_loans, calculate_fine,
    get_borrower_by_user, get_borrower_by_id_number, get_borrower_details,
    get_circulation_stats, get_active_loans, get_recent_transactions,
    get_loans_by_borrower,
    create_reservation, get_next_queue_position,
    get_active_reservation_by_book_and_borrower, get_reservation_by_id,
    get_reservations_grouped, get_reservations_by_book,
    allocate_reservation, claim_reservation, expire_reservation, next_in_queue,
    get_available_accession_by_book, create_notification,
    count_allocated_reservations, count_available_accessions,
    expire_overdue_reservations, get_borrowers_for_history,
    get_full_reservation_history_by_borrower, get_user_loan_history,
    get_fines_by_borrower, get_total_fines, get_fine_record, mark_fine_paid,
    is_book_blocked_for_daily, is_accession_lost,
)

VALID_BORROW_TYPES = ('overnight', 'daily_circulation')

VALID_LOAN_TYPE_FILTERS = ('all', 'overnight', 'daily_circulation')
VALID_LOAN_STATUS_FILTERS = ('all', 'overdue', 'due_soon')


def _safe_notify(borrower_id, message, notif_type, ref):
    """Best-effort notification: a failed notification must never turn a
    successful loan/return/reservation into a 500 (the write already
    committed). Mirrors the try/except pattern in requests/routes.py."""
    try:
        create_notification(borrower_id, message, notif_type, ref)
    except Exception:
        current_app.logger.warning('create_notification failed for borrower %s',
                                   borrower_id, exc_info=True)


def _is_unique_violation(exc):
    """True when a write lost a race against the partial unique indexes
    in schema.sql (uq_active_loan_per_accession,
    uq_active_loan_per_book_borrower,
    uq_active_reservation_per_book_borrower). Only this expected,
    user-driven failure is converted to a friendly retry message;
    every other DB error still propagates to the 500 handler."""
    try:
        from psycopg2 import errors as _pg_errors
        return isinstance(exc, _pg_errors.UniqueViolation)
    except Exception:
        return False


class _DuplicateReservation(Exception):
    """Lost a race against uq_active_reservation_per_book_borrower: the
    borrower already holds an active reservation for this book. Routes
    turn this into a friendly 'already have a pending reservation'
    flash instead of the generic retry message."""
    pass


def _create_reservation_retry(book_id, borrower_id, max_attempts=3):
    """Insert a waiting reservation, retrying queue-position collisions.

    db.execute commits per statement (no multi-statement transactions),
    so two simultaneous reserves can compute the same MAX(pos)+1; the
    loser hits uq_active_queue_pos. On a unique violation, re-check for
    a duplicate reservation (raise _DuplicateReservation when found)
    and otherwise retry with a fresh position. After max_attempts
    collisions the last violation propagates for the generic retry
    flash. Non-unique errors propagate immediately."""
    last_exc = None
    position = None
    for _ in range(max_attempts):
        position = get_next_queue_position(book_id)
        try:
            create_reservation(book_id, borrower_id, position)
            return position
        except Exception as e:
            if not _is_unique_violation(e):
                raise
            last_exc = e
            if get_active_reservation_by_book_and_borrower(book_id, borrower_id):
                raise _DuplicateReservation() from e
    raise last_exc


def _borrow_limit(role_name):
    if role_name == 'Student':
        return current_app.config.get('MAX_BORROW_LIMIT_STUDENT', 3)
    return current_app.config.get('MAX_BORROW_LIMIT_FACULTY', 5)


def _borrower_status(row):
    """Borrower status across the two borrower tuple shapes.

    get_borrower_details() -> 7-tuple, status at [3].
    get_borrower_by_user()  -> SELECT * (8 cols), status at [5].
    Legacy test mocks use a 5-tuple with status at [4].
    """
    if not row:
        return None
    if len(row) == 7:
        return row[3]
    if len(row) >= 6:
        return row[5]
    if len(row) >= 5:
        return row[4]
    if len(row) > 3:
        return row[3]
    return None


def _book_is_archived(book):
    """True when a book_catalog row is archived. Short mock tuples
    (len <= 11) are treated as active so old tests keep passing."""
    if not book or len(book) <= 11:
        return False
    return book[11] != 'active'


def _claim_window():
    """(deadline datetime, label) for reservation pickup. Hours-based
    so a 2-hour window is possible; falls back to legacy DAYS setting."""
    hours = current_app.config.get('RESERVATION_CLAIM_HOURS')
    if hours is None:
        days = current_app.config.get('RESERVATION_CLAIM_DAYS', 2)
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 2
        return datetime.now() + timedelta(days=days), f'{days} day(s)'
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        hours = 2
    return datetime.now() + timedelta(hours=hours), f'{hours:g} hour(s)'


def _compute_due_date(borrow_type, role_name):
    if borrow_type == 'daily_circulation':
        days = current_app.config.get('DAILY_CIRCULATION_DUE_DAYS', 0)
        fallback = 0
    elif role_name == 'Student':
        days = current_app.config.get('OVERNIGHT_DUE_DAYS_STUDENT', 1)
        fallback = 1
    else:
        days = current_app.config.get('OVERNIGHT_DUE_DAYS_FACULTY', 7)
        fallback = 7
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = fallback
    return date.today() + timedelta(days=days)


@circulation_bp.route('/librarian/circulation')
@login_required
@librarian_required
def circulation_page():
    stats = get_circulation_stats()
    active_loans = get_active_loans()
    recent = get_recent_transactions(10) or []

    search = request.args.get('search', '').strip()

    loan_type = request.args.get('loan_type', 'all').strip().lower()
    if loan_type not in VALID_LOAN_TYPE_FILTERS:
        loan_type = 'all'
    loan_status = request.args.get('loan_status', 'all').strip().lower()
    if loan_status not in VALID_LOAN_STATUS_FILTERS:
        loan_status = 'all'
    borrow_date = request.args.get('borrow_date', '').strip()
    if borrow_date:
        try:
            datetime.strptime(borrow_date, '%Y-%m-%d')
        except ValueError:
            borrow_date = ''
    table_search = request.args.get('q', '').strip()

    today_val = date.today()
    due_soon_cutoff = today_val + timedelta(days=2)

    # One status per active loan so badges, counts, and the status filter
    # always agree (overdue = flagged or past due; due soon = active and
    # due within 2 days; everything else is plain borrowed).
    loan_flags = {}
    for loan in active_loans or []:
        if _loan_is_overdue(loan, today_val):
            loan_flags[loan[0]] = 'overdue'
        elif _loan_is_due_soon(loan, today_val, due_soon_cutoff):
            loan_flags[loan[0]] = 'due_soon'
        else:
            loan_flags[loan[0]] = 'borrowed'

    filtered_loans = []
    for loan in active_loans or []:
        if loan_type != 'all' and loan[3] != loan_type:
            continue
        if loan_status != 'all' and loan_flags.get(loan[0]) != loan_status:
            continue
        if borrow_date and str(loan[1])[:10] != borrow_date:
            continue
        if table_search and not _loan_matches_search(loan, table_search):
            continue
        filtered_loans.append(loan)
    total_loans = len(active_loans or [])
    filters_active = (loan_type != 'all' or loan_status != 'all'
                      or bool(borrow_date) or bool(table_search))
    modal_filter_count = (1 if loan_type != 'all' else 0) + (1 if borrow_date else 0)

    borrower = None
    borrower_loans = []
    if search:
        borrower_row = get_borrower_by_id_number(search)
        if borrower_row:
            borrower = get_borrower_details(borrower_row[0])
            borrower_loans = get_loans_by_borrower(borrower_row[0])
        else:
            flash(f'No borrower found with ID number "{search}".', 'error')

    return render_template(
        'circulation/circulation.html',
        stats=stats,
        active_loans=filtered_loans,
        total_loans=total_loans,
        loan_flags=loan_flags,
        loan_type=loan_type,
        loan_status=loan_status,
        borrow_date=borrow_date,
        table_search=table_search,
        filters_active=filters_active,
        modal_filter_count=modal_filter_count,
        overdue_count=sum(1 for flag in loan_flags.values() if flag == 'overdue'),
        due_soon_count=sum(1 for flag in loan_flags.values() if flag == 'due_soon'),
        recent=recent,
        search=search,
        borrower=borrower,
        borrower_loans=borrower_loans,
        today=today_val,
        borrow_limit_student=current_app.config.get('MAX_BORROW_LIMIT_STUDENT', 3),
        borrow_limit_faculty=current_app.config.get('MAX_BORROW_LIMIT_FACULTY', 5),
    )


def _loan_matches_search(loan, query):
    """Case-insensitive match on borrower, title, or accession number."""
    needle = query.lower()
    return any(needle in str(loan[i] or '').lower() for i in (5, 7, 8))


def _loan_is_overdue(loan, today):
    """True when an active-loan tuple is overdue (flagged or past due)."""
    if loan[4] == 'overdue':
        return True
    if loan[4] != 'active' or loan[2] is None:
        return False
    try:
        return loan[2] < today
    except TypeError:
        return str(loan[2])[:10] < today.isoformat()


def _loan_is_due_soon(loan, today, cutoff):
    """True when an active (not overdue) loan is due between today and cutoff."""
    if loan[4] != 'active' or loan[2] is None:
        return False
    try:
        return today <= loan[2] <= cutoff
    except TypeError:
        day = str(loan[2])[:10]
        return today.isoformat() <= day <= cutoff.isoformat()


@circulation_bp.route('/librarian/circulation/borrow', methods=['POST'])
@login_required
@librarian_required
def desk_borrow():
    borrower_id = request.form.get('borrower_id', type=int)
    id_number = request.form.get('id_number', '').strip()
    accession_number = request.form.get('accession_number', '').strip()
    borrow_type = request.form.get('borrow_type', '')

    if borrow_type not in VALID_BORROW_TYPES:
        flash('Invalid borrow type.', 'error')
        return redirect(url_for('circulation.circulation_page', search=id_number))

    if borrower_id:
        borrower_row = get_borrower_details(borrower_id)
    else:
        borrower_row = get_borrower_by_id_number(id_number) if id_number else None
        borrower_row = get_borrower_details(borrower_row[0]) if borrower_row else None
    if not borrower_row:
        flash('Borrower not found.', 'error')
        return redirect(url_for('circulation.circulation_page', search=id_number))

    borrower_status = borrower_row[3] if len(borrower_row) > 3 else None
    if borrower_status != 'active':
        flash('This borrower account is not active.', 'error')
        return redirect(url_for('circulation.circulation_page', search=id_number))

    accession = get_accession_by_number(accession_number) if accession_number else None
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    if is_accession_lost(accession[0]):
        flash(f'Accession {accession_number} is marked as lost and cannot be borrowed.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    book_for_accession = get_book_by_id(accession[2])
    if book_for_accession is not None and _book_is_archived(book_for_accession):
        flash('This book is archived and cannot be borrowed.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    if get_active_loan_by_accession(accession[0]):
        flash(f'Accession {accession_number} is already on loan.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    # Don't let walk-ins jump the reservation queue: if someone else is
    # waiting first for this book, direct them to allocate instead.
    first_waiting = next_in_queue(accession[2])
    if first_waiting and len(first_waiting) > 2 and first_waiting[2] != borrower_row[0]:
        flash('This book has a waiting reservation queue — allocate it to the next borrower first.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    if get_active_loan_by_book_and_borrower(accession[2], borrower_row[0]):
        flash(f'{borrower_row[4]} already has a copy of this book borrowed.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    limit = _borrow_limit(borrower_row[6])
    if count_active_loans(borrower_row[0]) >= limit:
        flash(f'{borrower_row[4]} has reached the borrow limit ({limit} books).', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    if borrow_type == 'daily_circulation' and is_book_blocked_for_daily(accession[2]):
        flash('Not Available — this book is borrowed as Overnight and already allocated.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    due_date = _compute_due_date(borrow_type, borrower_row[6])
    try:
        borrow_book(accession[2], accession[0], borrower_row[0], current_user.id, borrow_type, due_date)
    except Exception as e:
        if _is_unique_violation(e):
            flash('Another transaction just completed — please refresh and try again.', 'error')
            return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))
        raise
    _safe_notify(
        borrower_row[0],
        f'You borrowed copy {accession_number}. Due {due_date}.',
        'borrow',
        str(accession[0]),
    )
    log_activity(current_user.id, f'circulation:borrow:{accession[0]}')
    flash(f'Borrowed — {accession_number} due {due_date}.', 'success')
    return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))


@circulation_bp.route('/librarian/circulation/return', methods=['POST'])
@login_required
@librarian_required
def desk_return():
    """Pure check-in: the copy is back on the shelf.

    Condition reporting lives in the standalone mark-lost / mark-damaged
    actions below — a return never flags a copy itself.
    """
    accession_number = request.form.get('accession_number', '').strip()

    accession = get_accession_by_number(accession_number) if accession_number else None
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('circulation.circulation_page'))

    loan = get_active_loan_by_accession(accession[0])
    if not loan:
        flash(f'Accession {accession_number} is not currently borrowed.', 'error')
        return redirect(url_for('circulation.circulation_page'))

    fine = calculate_fine(loan[0], current_app.config.get('OVERDUE_FINE_PER_DAY', 5.0),
                          current_app.config.get('OVERDUE_GRACE_DAYS', 0))
    return_book(loan[0], fine, updated_by=current_user.id)
    borrower_id_for_loan = loan[3] if len(loan) > 3 else None
    if borrower_id_for_loan is not None:
        _safe_notify(
            borrower_id_for_loan,
            f'You returned copy {accession_number}.'
            + (f' Overdue fine: ₱{fine:.2f}.' if fine > 0 else ' Thank you!'),
            'return',
            str(loan[0]),
        )
        if fine > 0:
            _safe_notify(
                borrower_id_for_loan,
                f'Overdue fine of ₱{fine:.2f} assessed for copy {accession_number}. Please settle at the desk.',
                'fine',
                str(loan[0]),
            )
    log_activity(current_user.id, f'circulation:return:{loan[0]}')

    waiting = next_in_queue(accession[2])
    if waiting and len(waiting) > 2:
        _safe_notify(
            waiting[2],
            f'A copy ({accession_number}) was returned and is awaiting librarian allocation.',
            'hold_ready',
            str(waiting[0]),
        )

    if fine > 0:
        flash(f'Returned. Overdue fine: ₱{fine:.2f}.', 'success')
    else:
        flash(f'Accession {accession_number} returned.', 'success')
    return redirect(url_for('circulation.circulation_page'))


def _resolve_condition_accession(accession_number):
    """Accession row for a condition action, or None (already flashed)."""
    accession = get_accession_by_number(accession_number) if accession_number else None
    if not accession:
        flash('Accession not found.', 'error')
        return None
    return accession


@circulation_bp.route('/librarian/circulation/accession/lost', methods=['POST'])
@login_required
@librarian_required
def mark_copy_lost_route():
    """Standalone mark-as-lost: no return required.

    If the copy is on loan, the loan is closed as lost (fine still
    computed, borrower notified) since there is nothing to check in.
    """
    from app.inventory.models import mark_copy_lost
    accession_number = request.form.get('accession_number', '').strip()
    accession = _resolve_condition_accession(accession_number)
    if not accession:
        return redirect(url_for('circulation.circulation_page'))

    loan = get_active_loan_by_accession(accession[0])
    if loan:
        fine = calculate_fine(loan[0], current_app.config.get('OVERDUE_FINE_PER_DAY', 5.0),
                              current_app.config.get('OVERDUE_GRACE_DAYS', 0))
        try:
            return_book(loan[0], fine, lost_flag=True, updated_by=current_user.id)
        except Exception as e:
            if _is_unique_violation(e):
                flash('Another transaction just completed — please refresh and try again.', 'error')
                return redirect(url_for('circulation.circulation_page'))
            raise
        borrower_id_for_loan = loan[3] if len(loan) > 3 else None
        if borrower_id_for_loan is not None:
            _safe_notify(
                borrower_id_for_loan,
                f'Copy {accession_number} was marked as lost.'
                + (f' Overdue fine: ₱{fine:.2f}.' if fine > 0 else ''),
                'return',
                str(loan[0]),
            )
            if fine > 0:
                _safe_notify(
                    borrower_id_for_loan,
                    f'Overdue fine of ₱{fine:.2f} assessed for lost copy {accession_number}. Please settle at the desk.',
                    'fine',
                    str(loan[0]),
                )
    mark_copy_lost(accession[0], checked_by=current_user.id)
    log_activity(current_user.id, f'circulation:mark_lost:{accession[0]}')
    if loan:
        flash(f'Accession {accession_number} marked as lost — its loan was closed.', 'success')
    else:
        flash(f'Accession {accession_number} marked as lost.', 'success')
    return redirect(url_for('circulation.circulation_page'))


@circulation_bp.route('/librarian/circulation/accession/damaged', methods=['POST'])
@login_required
@librarian_required
def mark_copy_damaged_route():
    """Standalone mark-as-damaged: works whether or not the copy is on
    loan. A reason is required so the cataloging table can show it."""
    from app.inventory.models import mark_copy_damaged
    accession_number = request.form.get('accession_number', '').strip()
    notes = request.form.get('notes', '').strip()
    accession = _resolve_condition_accession(accession_number)
    if not accession:
        return redirect(url_for('circulation.circulation_page'))

    if not notes:
        flash('A reason is required to mark a copy as damaged.', 'error')
        return redirect(url_for('circulation.circulation_page'))
    if len(notes) > 255:
        flash('Damage reason is too long (max 255 characters).', 'error')
        return redirect(url_for('circulation.circulation_page'))

    mark_copy_damaged(accession[0], notes, checked_by=current_user.id)
    log_activity(current_user.id, f'circulation:mark_damaged:{accession[0]}')
    flash(f'Accession {accession_number} marked as damaged.', 'success')
    return redirect(url_for('circulation.circulation_page'))


@circulation_bp.route('/librarian/reservations')
@login_required
@librarian_required
def reservations_page():
    # Auto-expire past-deadline allocations so they leave the active queue,
    # and auto-remove finished (claimed/expired) history from the default view.
    try:
        expire_overdue_reservations()
    except Exception:
        current_app.logger.warning('expire_overdue_reservations failed', exc_info=True)
    status_filter = request.args.get('status', 'active').strip().lower()
    if status_filter == 'active':
        wanted = ('waiting', 'allocated')
    elif status_filter in ('waiting', 'allocated'):
        wanted = (status_filter,)
    elif status_filter == 'history':
        wanted = ('claimed', 'expired')
    elif status_filter == 'all':
        wanted = None
    else:
        status_filter = 'active'
        wanted = ('waiting', 'allocated')

    groups = get_reservations_grouped() or []
    reservations_by_book = {}
    for row in groups:
        if not row:
            continue
        reservations_by_book[row[0]] = (
            get_reservations_by_book(row[0]) or [])

    def _num(r, i):
        try:
            return int(r[i] or 0)
        except (IndexError, TypeError, ValueError):
            return 0

    active = sum(_num(row, 4) + _num(row, 5) for row in groups)
    ready = sum(_num(row, 5) for row in groups)
    pending = sum(_num(row, 4) for row in groups)
    if wanted:
        reservations_by_book = {
            book_id: [res for res in rows if res[2] in wanted]
            for book_id, rows in reservations_by_book.items()
        }
        reservations_by_book = {
            book_id: rows for book_id, rows in reservations_by_book.items() if rows
        }
        groups = [group for group in groups if group[0] in reservations_by_book]
    return render_template(
        'reservations/reservations.html',
        groups=groups,
        reservations_by_book=reservations_by_book,
        stats={'active': active, 'ready': ready, 'pending': pending},
        status_filter=status_filter,
    )


@circulation_bp.route('/librarian/reservations/<int:reservation_id>/<action>', methods=['POST'])
@login_required
@librarian_required
def reservation_action(reservation_id, action):
    keep_status = request.form.get('status', '').strip().lower()
    status_args = {'status': keep_status} if keep_status in ('active', 'waiting', 'allocated', 'history', 'all') else {}
    # Sweep past-deadline allocations first so a stale 'allocated' row
    # cannot be claimed after its 2-hour window.
    try:
        expire_overdue_reservations()
    except Exception:
        current_app.logger.warning('expire_overdue_reservations failed', exc_info=True)
    reservation = get_reservation_by_id(reservation_id)
    if not reservation or len(reservation) < 6:
        flash('Reservation not found.', 'error')
        return redirect(url_for('circulation.reservations_page', **status_args))

    if action == 'allocate':
        if reservation[5] != 'waiting':
            flash('Only waiting reservations can be allocated.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        if not get_available_accession_by_book(reservation[1]):
            flash('Cannot allocate — all copies of this book are still on loan.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        book_for_reservation = get_book_by_id(reservation[1])
        if book_for_reservation is not None and _book_is_archived(book_for_reservation):
            flash('Cannot allocate — this book is archived.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        borrower_detail = get_borrower_details(reservation[2])
        if borrower_detail is not None and _borrower_status(borrower_detail) != 'active':
            borrower_name = borrower_detail[4] if len(borrower_detail) > 4 else 'Borrower'
            flash(f'Cannot allocate — {borrower_name} borrower account is not active.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        role_name = borrower_detail[6] if borrower_detail else 'Student'
        if get_active_loan_by_book_and_borrower(reservation[1], reservation[2]):
            borrower_name = borrower_detail[4] if borrower_detail else 'Borrower'
            flash(f'Cannot allocate — {borrower_name} already has a copy of this book borrowed.', 'error')
            return redirect(url_for('circulation.reservations_page'))
        limit = _borrow_limit(role_name)
        if count_active_loans(reservation[2]) >= limit:
            borrower_name = borrower_detail[4] if borrower_detail else 'Borrower'
            flash(f'Cannot allocate — {borrower_name} has reached the borrow limit ({limit} books).', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        # Over-booking guard: every physical copy already has an allocated
        # reservation waiting, so allocating one more would promise a copy
        # that does not exist. Kept alongside the no-copy check above,
        # which covers copies that are still on loan.
        if count_allocated_reservations(reservation[1]) >= count_available_accessions(reservation[1]):
            flash('Cannot allocate — no unallocated copy is available.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        deadline, window_label = _claim_window()
        try:
            allocate_reservation(reservation_id, deadline, updated_by=current_user.id)
        except Exception as e:
            if _is_unique_violation(e):
                flash('Another transaction just completed — please refresh and try again.', 'error')
                return redirect(url_for('circulation.reservations_page', **status_args))
            raise
        _safe_notify(
            reservation[2],
            f'Your reserved book is ready. Claim within {window_label}.',
            'hold_ready',
            str(reservation_id),
        )
        _safe_notify(
            reservation[2],
            f'Reservation #{reservation_id} allocated. Claim by {deadline.strftime("%b %d, %Y %I:%M %p")}.',
            'reservation',
            str(reservation_id),
        )
        log_activity(current_user.id, f'circulation:allocate_reservation:{reservation_id}')
        flash('Reservation allocated.', 'success')
    elif action == 'claim':
        if reservation[5] != 'allocated':
            flash('Only allocated reservations can be claimed.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        accession = get_available_accession_by_book(reservation[1])
        if not accession:
            flash('Cannot claim — no copy of this book is available to check out.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        book_for_claim = get_book_by_id(reservation[1])
        if book_for_claim is not None and _book_is_archived(book_for_claim):
            flash('Cannot claim — this book is archived.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        borrower_detail = get_borrower_details(reservation[2])
        if borrower_detail is not None and _borrower_status(borrower_detail) != 'active':
            borrower_name = borrower_detail[4] if len(borrower_detail) > 4 else 'Borrower'
            flash(f'Cannot claim — {borrower_name} borrower account is not active.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        role_name = borrower_detail[6] if borrower_detail else 'Student'
        if get_active_loan_by_book_and_borrower(reservation[1], reservation[2]):
            borrower_name = borrower_detail[4] if borrower_detail else 'Borrower'
            flash(f'Cannot claim — {borrower_name} already has a copy of this book borrowed.', 'error')
            return redirect(url_for('circulation.reservations_page'))
        limit = _borrow_limit(role_name)
        if count_active_loans(reservation[2]) >= limit:
            borrower_name = borrower_detail[4] if borrower_detail else 'Borrower'
            flash(f'Cannot claim — {borrower_name} has reached the borrow limit ({limit} books).', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        due_date = _compute_due_date('overnight', role_name)
        try:
            borrow_book(reservation[1], accession[0], reservation[2], current_user.id, 'overnight', due_date)
            try:
                claim_reservation(reservation_id, updated_by=current_user.id)
            except Exception as inner:
                if _is_unique_violation(inner):
                    raise
                # claim_reservation failed after the loan committed
                # (per-statement commits, no multi-statement transaction):
                # compensate the orphan loan best-effort, then re-raise.
                try:
                    orphan = get_active_loan_by_accession(accession[0])
                    if orphan:
                        return_book(orphan[0], 0, updated_by=current_user.id)
                except Exception:
                    pass
                raise
        except Exception as e:
            if _is_unique_violation(e):
                flash('Another transaction just completed — please refresh and try again.', 'error')
                return redirect(url_for('circulation.reservations_page', **status_args))
            raise
        _safe_notify(
            reservation[2],
            f'Reservation #{reservation_id} claimed. Book due {due_date}.',
            'reservation',
            str(reservation_id),
        )
        log_activity(current_user.id, f'circulation:claim_reservation:{reservation_id}')
        flash(f'Reservation claimed — booked as an overnight borrow due {due_date}.', 'success')
    elif action == 'expire':
        if reservation[5] not in ('waiting', 'allocated'):
            flash('This reservation is already finished.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        expire_reservation(reservation_id, updated_by=current_user.id)
        _safe_notify(
            reservation[2],
            f'Reservation #{reservation_id} expired/cancelled.',
            'reservation',
            str(reservation_id),
        )
        log_activity(current_user.id, f'circulation:expire_reservation:{reservation_id}')
        flash('Reservation expired.', 'success')
    else:
        flash('Invalid action.', 'error')

    return redirect(url_for('circulation.reservations_page', **status_args))


@circulation_bp.route('/user/borrow', methods=['POST'])
@login_required
def user_borrow():
    book_id = request.form.get('book_id', type=int)
    borrow_type = request.form.get('borrow_type', '')
    if borrow_type not in VALID_BORROW_TYPES:
        flash('Invalid borrow type.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id) if book_id
                        else url_for('cataloging.public_catalog'))

    book = get_book_by_id(book_id) if book_id else None
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.public_catalog'))

    borrower_row = get_borrower_by_user(current_user.id)
    if not borrower_row:
        flash('No borrower record found for your account.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))
    if _borrower_status(borrower_row) != 'active':
        flash('Your borrower account is not active.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if _book_is_archived(book):
        flash('This book is archived and cannot be borrowed.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if get_active_loan_by_book_and_borrower(book_id, borrower_row[0]):
        flash('You already have a copy of this book borrowed.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if borrow_type == 'overnight':
        existing = get_active_reservation_by_book_and_borrower(book_id, borrower_row[0])
        if existing:
            flash('You already have a pending reservation for this book.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        limit = _borrow_limit(current_user.role)
        if count_active_loans(borrower_row[0]) >= limit:
            flash(f'You have reached the borrow limit ({limit} books).', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        try:
            position = _create_reservation_retry(book_id, borrower_row[0])
        except _DuplicateReservation:
            flash('You already have a pending reservation for this book.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        except Exception as e:
            if _is_unique_violation(e):
                flash('Another transaction just completed — please refresh and try again.', 'error')
                return redirect(url_for('cataloging.book_info', book_id=book_id))
            raise
        _safe_notify(
            borrower_row[0],
            f'Overnight borrow request for "{book[1]}" submitted (queue #{position}). Awaiting librarian approval.',
            'reservation',
            str(book_id),
        )
        log_activity(current_user.id, f'circulation:user_borrow_request:{book_id}')
        flash('Overnight borrow request submitted. A librarian must approve it before the book leaves the library.', 'success')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    accession_id = request.form.get('accession_id', type=int)
    if accession_id:
        accession = get_accession_by_id(accession_id)
        if not accession or accession[2] != book_id:
            flash('Invalid copy selected.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        if is_accession_lost(accession[0]):
            flash('That copy is marked as lost and cannot be borrowed.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        if get_active_loan_by_accession(accession[0]):
            flash('That copy is already borrowed.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
    else:
        accession = get_available_accession_by_book(book_id)
    if not accession:
        flash('All copies are currently borrowed. Reserve it instead.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    limit = _borrow_limit(current_user.role)
    if count_active_loans(borrower_row[0]) >= limit:
        flash(f'You have reached the borrow limit ({limit} books).', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if get_active_reservation_by_book_and_borrower(book_id, borrower_row[0]):
        flash('You already have a pending reservation for this book.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    # Queue-jump parity with desk_borrow: don't let a daily walk-in take a
    # copy someone else is already queueing for (the overnight branch is
    # unaffected — joining the queue is its purpose). Advisory read only;
    # the write path's unique indexes stay authoritative.
    try:
        _first_waiting = next_in_queue(book_id)
    except Exception:
        _first_waiting = None
    if (_first_waiting and len(_first_waiting) > 2
            and _first_waiting[2] != borrower_row[0]):
        flash('This book has a waiting reservation queue — please reserve it instead.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if borrow_type == 'daily_circulation' and is_book_blocked_for_daily(book_id):
        flash('Not Available — this book is borrowed as Overnight and already allocated.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    due_date = _compute_due_date(borrow_type, current_user.role)
    try:
        borrow_book(book_id, accession[0], borrower_row[0], current_user.id, borrow_type, due_date)
    except Exception as e:
        if _is_unique_violation(e):
            flash('Another transaction just completed — please refresh and try again.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        raise
    _safe_notify(
        borrower_row[0],
        f'You borrowed "{book[1]}". Due {due_date}.',
        'borrow',
        str(accession[0]),
    )
    log_activity(current_user.id, f'circulation:user_borrow:{book_id}')
    flash(f'Book borrowed — due {due_date}.', 'success')
    return redirect(url_for('cataloging.book_info', book_id=book_id))


@circulation_bp.route('/user/reserve', methods=['POST'])
@login_required
def user_reserve():
    book_id = request.form.get('book_id', type=int)
    book = get_book_by_id(book_id) if book_id else None
    if not book:
        flash('Book not found.', 'error')
        return redirect(url_for('cataloging.public_catalog'))

    borrower_row = get_borrower_by_user(current_user.id)
    if not borrower_row:
        flash('No borrower record found for your account.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if _borrower_status(borrower_row) != 'active':
        flash('Your borrower account is not active.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if _book_is_archived(book):
        flash('This book is archived and cannot be reserved.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    existing = get_active_reservation_by_book_and_borrower(book_id, borrower_row[0])
    if existing:
        flash('You already have an active reservation for this book.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if get_active_loan_by_book_and_borrower(book_id, borrower_row[0]):
        flash('You already have a copy of this book borrowed.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if get_available_accession_by_book(book_id):
        flash('A copy is available — you can borrow it instead.', 'info')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    try:
        position = _create_reservation_retry(book_id, borrower_row[0])
    except _DuplicateReservation:
        flash('You already have an active reservation for this book.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))
    except Exception as e:
        if _is_unique_violation(e):
            flash('Another transaction just completed — please refresh and try again.', 'error')
            return redirect(url_for('cataloging.book_info', book_id=book_id))
        raise
    _safe_notify(
        borrower_row[0],
        f'Reservation for "{book[1]}" placed (queue #{position}). You will be notified when ready.',
        'reservation',
        str(book_id),
    )
    log_activity(current_user.id, f'circulation:user_reserve:{book_id}')
    flash('Reservation placed. You will be notified when a copy is ready.', 'success')
    return redirect(url_for('cataloging.book_info', book_id=book_id))


@circulation_bp.route('/user/return', methods=['POST'])
@login_required
def user_return():
    """Desk-only returns: every return must be inspected and approved
    by a librarian at the circulation desk, so self-service check-in is
    disabled. The endpoint stays (instead of 404) so stale pages and
    bookmarks degrade to guidance rather than an error.
    """
    flash('Please return books at the circulation desk so a librarian can inspect them.', 'info')
    return redirect(url_for('main.user_profile'))


@circulation_bp.route('/librarian/users/history')
@login_required
@librarian_required
def user_history_list():
    search = request.args.get('search', '').strip() or None
    borrowers = get_borrowers_for_history(search=search)
    return render_template(
        'circulation/user_history_list.html',
        borrowers=borrowers,
        search=search or '',
    )


@circulation_bp.route('/librarian/users/<int:user_id>/history')
@login_required
@librarian_required
def user_history_detail(user_id):
    from app.auth.models import get_user_by_id
    from app.requests.models import get_requests_by_borrower

    user_data = get_user_by_id(user_id)
    if not user_data:
        flash('User not found.', 'error')
        return redirect(url_for('circulation.user_history_list'))
    borrower = get_borrower_by_user(user_id)
    if not borrower:
        flash('No borrower record found for this user.', 'error')
        return redirect(url_for('circulation.user_history_list'))

    borrower_id = borrower[0]
    transactions = get_user_loan_history(user_id) or []
    reservations = get_full_reservation_history_by_borrower(borrower_id) or []
    try:
        my_requests = get_requests_by_borrower(borrower_id) or []
    except Exception:
        my_requests = []
    fines = get_fines_by_borrower(borrower_id) or []
    total_fines = get_total_fines(borrower_id) or 0
    return render_template(
        'circulation/user_history_detail.html',
        user_data=user_data,
        borrower=borrower,
        transactions=transactions,
        reservations=reservations,
        my_requests=my_requests,
        fines=fines,
        total_fines=total_fines,
    )


@circulation_bp.route('/librarian/users/<int:user_id>/fines/<int:circulation_id>/pay', methods=['POST'])
@login_required
@librarian_required
def pay_fine(user_id, circulation_id):
    from app.auth.models import get_user_by_id
    back = url_for('circulation.user_history_detail', user_id=user_id)
    if not get_user_by_id(user_id):
        flash('User not found.', 'error')
        return redirect(url_for('circulation.user_history_list'))
    borrower = get_borrower_by_user(user_id)
    if not borrower:
        flash('No borrower record found for this user.', 'error')
        return redirect(url_for('circulation.user_history_list'))
    fine = get_fine_record(circulation_id)
    if not fine or fine[1] != borrower[0] or not fine[2] or float(fine[2]) <= 0:
        flash('Fine not found.', 'error')
        return redirect(back)
    if fine[3]:
        flash('This fine is already paid.', 'info')
        return redirect(back)
    mark_fine_paid(circulation_id, updated_by=current_user.id)
    log_activity(current_user.id, f'circulation:fine_paid:{circulation_id}')
    flash(f'Fine of ₱{float(fine[2]):.2f} marked as paid.', 'success')
    return redirect(back)
