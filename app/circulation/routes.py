from datetime import date, timedelta, datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import circulation_bp
from app.auth.decorators import librarian_required
from app.auth.models import log_activity
from app.cataloging.models import get_book_by_id, get_accession_by_number, get_accession_by_id
from .models import (
    borrow_book, return_book, get_active_loan_by_accession,
    count_active_loans, calculate_fine,
    get_borrower_by_user, get_borrower_by_id_number, get_borrower_details,
    get_circulation_stats, get_active_loans, get_recent_transactions,
    get_overdue_loans_detail, get_due_soon_detail, get_loans_by_borrower,
    get_active_loan_by_id_and_user,
    create_reservation, get_next_queue_position,
    get_active_reservation_by_book_and_borrower, get_reservation_by_id,
    get_reservations_grouped, get_reservations_by_book,
    allocate_reservation, claim_reservation, expire_reservation, next_in_queue,
    get_available_accession_by_book, create_notification,
    get_user_active_loans, get_active_loan_by_id_and_user,
)

VALID_BORROW_TYPES = ('overnight', 'daily_circulation')


def _borrow_limit(role_name):
    if role_name == 'Student':
        return current_app.config['MAX_BORROW_LIMIT_STUDENT']
    return current_app.config['MAX_BORROW_LIMIT_FACULTY']


def _compute_due_date(borrow_type, role_name):
    if borrow_type == 'daily_circulation':
        days = current_app.config['DAILY_CIRCULATION_DUE_DAYS']
    elif role_name == 'Student':
        days = current_app.config['OVERNIGHT_DUE_DAYS_STUDENT']
    else:
        days = current_app.config['OVERNIGHT_DUE_DAYS_FACULTY']
    return date.today() + timedelta(days=days)


@circulation_bp.route('/librarian/circulation')
@login_required
@librarian_required
def circulation_page():
    stats = get_circulation_stats()
    active_loans = get_active_loans()
    recent = get_recent_transactions(10)
    overdue = get_overdue_loans_detail()
    due_soon = get_due_soon_detail(2)

    search = request.args.get('search', '').strip()
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
        active_loans=active_loans,
        recent=recent,
        overdue=overdue,
        due_soon=due_soon,
        search=search,
        borrower=borrower,
        borrower_loans=borrower_loans,
        today=date.today(),
        borrow_limit_student=current_app.config['MAX_BORROW_LIMIT_STUDENT'],
        borrow_limit_faculty=current_app.config['MAX_BORROW_LIMIT_FACULTY'],
    )


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

    if borrower_row[3] != 'active':
        flash('This borrower account is not active.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    accession = get_accession_by_number(accession_number) if accession_number else None
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    if get_active_loan_by_accession(accession[0]):
        flash(f'Accession {accession_number} is already on loan.', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    limit = _borrow_limit(borrower_row[6])
    if count_active_loans(borrower_row[0]) >= limit:
        flash(f'{borrower_row[4]} has reached the borrow limit ({limit} books).', 'error')
        return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))

    due_date = _compute_due_date(borrow_type, borrower_row[6])
    borrow_book(accession[2], accession[0], borrower_row[0], current_user.id, borrow_type, due_date)
    log_activity(current_user.id, f'circulation:borrow:{accession[0]}')
    flash(f'Borrowed — {accession_number} due {due_date}.', 'success')
    return redirect(url_for('circulation.circulation_page', search=borrower_row[1]))


@circulation_bp.route('/librarian/circulation/return', methods=['POST'])
@login_required
@librarian_required
def desk_return():
    accession_number = request.form.get('accession_number', '').strip()
    damage_notes = request.form.get('damage_notes', '').strip() or None
    lost_flag = request.form.get('lost') == '1'

    accession = get_accession_by_number(accession_number) if accession_number else None
    if not accession:
        flash('Accession not found.', 'error')
        return redirect(url_for('circulation.circulation_page'))

    loan = get_active_loan_by_accession(accession[0])
    if not loan:
        flash(f'Accession {accession_number} is not currently borrowed.', 'error')
        return redirect(url_for('circulation.circulation_page'))

    fine = calculate_fine(loan[0], current_app.config['OVERDUE_FINE_PER_DAY'])
    return_book(loan[0], fine, damage_notes, lost_flag)
    log_activity(current_user.id, f'circulation:return:{loan[0]}')

    waiting = next_in_queue(accession[2])
    if waiting:
        create_notification(
            waiting[2],
            f'A reserved copy of "{get_book_by_id(accession[2])[1]}" is ready for pickup.',
            'hold_ready',
            str(waiting[0]),
        )

    if lost_flag:
        flash(f'Accession {accession_number} marked as lost.', 'success')
    elif fine > 0:
        flash(f'Returned. Overdue fine: ₱{fine:.2f}.', 'success')
    else:
        flash(f'Accession {accession_number} returned.', 'success')
    return redirect(url_for('circulation.circulation_page'))


@circulation_bp.route('/librarian/reservations')
@login_required
@librarian_required
def reservations_page():
    status_filter = request.args.get('status', '').strip().lower()
    if status_filter == 'active':
        wanted = ('waiting', 'allocated')
    elif status_filter in ('waiting', 'allocated'):
        wanted = (status_filter,)
    else:
        status_filter = ''
        wanted = None

    groups = get_reservations_grouped()
    reservations_by_book = {
        row[0]: get_reservations_by_book(row[0]) for row in groups
    }
    active = sum(row[4] + row[5] for row in groups)
    ready = sum(row[5] for row in groups)
    pending = sum(row[4] for row in groups)
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
    status_args = {'status': keep_status} if keep_status in ('active', 'waiting', 'allocated') else {}
    reservation = get_reservation_by_id(reservation_id)
    if not reservation:
        flash('Reservation not found.', 'error')
        return redirect(url_for('circulation.reservations_page', **status_args))

    if action == 'allocate':
        if reservation[5] != 'waiting':
            flash('Only waiting reservations can be allocated.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        if not get_available_accession_by_book(reservation[1]):
            flash('Cannot allocate — all copies of this book are still on loan.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        borrower_detail = get_borrower_details(reservation[2])
        role_name = borrower_detail[6] if borrower_detail else 'Student'
        limit = _borrow_limit(role_name)
        if count_active_loans(reservation[2]) >= limit:
            borrower_name = borrower_detail[4] if borrower_detail else 'Borrower'
            flash(f'Cannot allocate — {borrower_name} has reached the borrow limit ({limit} books).', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        deadline = datetime.now() + timedelta(days=2)
        allocate_reservation(reservation_id, deadline)
        create_notification(
            reservation[2],
            f'Your reserved book is ready. Claim within 2 days.',
            'hold_ready',
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
        borrower_detail = get_borrower_details(reservation[2])
        role_name = borrower_detail[6] if borrower_detail else 'Student'
        limit = _borrow_limit(role_name)
        if count_active_loans(reservation[2]) >= limit:
            borrower_name = borrower_detail[4] if borrower_detail else 'Borrower'
            flash(f'Cannot claim — {borrower_name} has reached the borrow limit ({limit} books).', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        due_date = _compute_due_date('overnight', role_name)
        borrow_book(reservation[1], accession[0], reservation[2], current_user.id, 'overnight', due_date)
        claim_reservation(reservation_id)
        log_activity(current_user.id, f'circulation:claim_reservation:{reservation_id}')
        flash(f'Reservation claimed — booked as an overnight borrow due {due_date}.', 'success')
    elif action == 'expire':
        if reservation[5] not in ('waiting', 'allocated'):
            flash('This reservation is already finished.', 'error')
            return redirect(url_for('circulation.reservations_page', **status_args))
        expire_reservation(reservation_id)
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
    if borrower_row[4] != 'active':
        flash('Your borrower account is not active.', 'error')
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
        position = get_next_queue_position(book_id)
        create_reservation(book_id, borrower_row[0], position)
        log_activity(current_user.id, f'circulation:user_borrow_request:{book_id}')
        flash('Overnight borrow request submitted. A librarian must approve it before the book leaves the library.', 'success')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    accession_id = request.form.get('accession_id', type=int)
    if accession_id:
        accession = get_accession_by_id(accession_id)
        if not accession or accession[2] != book_id:
            flash('Invalid copy selected.', 'error')
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

    due_date = _compute_due_date(borrow_type, current_user.role)
    borrow_book(book_id, accession[0], borrower_row[0], current_user.id, borrow_type, due_date)
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

    existing = get_active_reservation_by_book_and_borrower(book_id, borrower_row[0])
    if existing:
        flash('You already have an active reservation for this book.', 'error')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    if get_available_accession_by_book(book_id):
        flash('A copy is available — you can borrow it instead.', 'info')
        return redirect(url_for('cataloging.book_info', book_id=book_id))

    position = get_next_queue_position(book_id)
    create_reservation(book_id, borrower_row[0], position)
    log_activity(current_user.id, f'circulation:user_reserve:{book_id}')
    flash('Reservation placed. You will be notified when a copy is ready.', 'success')
    return redirect(url_for('cataloging.book_info', book_id=book_id))


@circulation_bp.route('/user/return', methods=['POST'])
@login_required
def user_return():
    circulation_id = request.form.get('circulation_id', type=int)
    if not circulation_id:
        flash('Invalid borrowing record.', 'error')
        return redirect(url_for('main.user_profile'))

    loan = get_active_loan_by_id_and_user(circulation_id, current_user.id)
    if not loan:
        flash('Borrowing record not found or already returned.', 'error')
        return redirect(url_for('main.user_profile'))

    if len(loan) > 5 and loan[5] == 'overnight':
        flash('Overnight books must be returned at the circulation desk for inspection.', 'error')
        return redirect(url_for('main.user_profile'))

    fine = calculate_fine(loan[0], current_app.config['OVERDUE_FINE_PER_DAY'])
    return_book(loan[0], fine)
    log_activity(current_user.id, f'circulation:user_return:{loan[0]}')

    waiting = next_in_queue(loan[1])
    if waiting:
        create_notification(
            waiting[2],
            f'A reserved copy of "{get_book_by_id(loan[1])[1]}" is ready for pickup.',
            'hold_ready',
            str(waiting[0]),
        )

    if fine > 0:
        flash(f'Book returned. Overdue fine: ₱{fine:.2f}.', 'success')
    else:
        flash('Book returned.', 'success')
    return redirect(url_for('main.user_profile'))
