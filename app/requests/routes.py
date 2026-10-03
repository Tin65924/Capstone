from app.procurement.models import create_procurement
from app.auth.models import log_activity
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from . import requests_bp
from .models import (
    create_request, get_requests, get_request_by_id,
    update_request_status, get_demand_by_role, get_borrower_by_user,
    check_duplicate_request, check_catalog_exists,
    check_approved_request_exists, get_requests_with_details, get_requests_by_borrower,
    count_requests, count_requests_by_status, build_stacked_chart, build_variant_lookup,
    _cluster_demand, normalize_title, PER_PAGE
)
from app.auth.decorators import librarian_required


# Legacy 'existing_in_collection' rows still sort last under "All" and render
# with the generic badge; the status can no longer be created or filtered.
VALID_STATUSES = ['pending_review', 'approved', 'rejected', 'procured']

@requests_bp.route('/librarian/requests')
@login_required
@librarian_required
def list_requests():
    status = request.args.get('status', 'pending_review')
    if status == 'all':
        status = None
    elif status not in VALID_STATUSES:
        status = 'pending_review'

    search = request.args.get('search', '').strip() or None

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    sort = request.args.get('sort', 'demand')
    if sort not in ('demand', 'recent'):
        sort = 'demand'

    items = get_requests_with_details(status=status, search=search, page=page) or []
    total = count_requests(status=status, search=search)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    # Headline stat cards (unfiltered): one COUNT per status via a single
    # GROUP BY query (legacy 'existing_in_collection' folds into the total).
    status_counts = count_requests_by_status()
    total_all = sum(status_counts.values())
    pending_count = status_counts.get('pending_review', 0)
    approved_count = status_counts.get('approved', 0)
    rejected_count = status_counts.get('rejected', 0)
    procured_count = status_counts.get('procured', 0)

    # Global demand (pending + approved) drives both the overview chart
    # and every card's bar, so typo variants ("Introductin" vs
    # "Introduction") merge through one clustering pass.
    demand_rows = get_demand_by_role() or []
    variant_lookup = build_variant_lookup(demand_rows)

    # Stacked-bar overview: one bar per requested title, split into
    # Student / Faculty / Other (staff) segments so acquisition priority
    # (both sides requesting) is visible at a glance.
    demand_chart = []
    for display_title, student_count, faculty_count, other_count, total_count in build_stacked_chart(demand_rows, limit=10):
        if total_count <= 0:
            continue
        student_pct = round(student_count / total_count * 100, 1)
        faculty_pct = round(faculty_count / total_count * 100, 1)
        other_pct = round(max(other_count, 0) / total_count * 100, 1)
        demand_chart.append({
            'title': display_title,
            'student': student_count,
            'faculty': faculty_count,
            'other': max(other_count, 0),
            'total': total_count,
            'student_pct': student_pct,
            'faculty_pct': faculty_pct,
            'other_pct': other_pct,
            'both': student_count > 0 and faculty_count > 0,
        })

    # Grouped cards: one card per logical title (fuzzy-merged), not one
    # per request row, so 5 requests for the same book render once with
    # Approve-all / Reject-all. Groups are built from the current page
    # (defense scale fits one page); global counts come from the lookup.
    groups = _build_card_groups(items, variant_lookup)
    if sort == 'demand':
        groups.sort(key=lambda g: (-g['total'], g['display'].lower()))
    else:
        groups.sort(key=lambda g: (g['newest_key'], g['display'].lower()), reverse=True)

    # Legacy per-row list kept for backwards compatibility.
    demand_by_title = {}
    for title, role_name, count in demand_rows:
        demand_by_title.setdefault(title, {})[role_name] = count
    requests_with_demand = [
        (r, demand_by_title.get(r[2], {})) for r in items
    ]

    return render_template(
        'requests/requests.html',
        requests=requests_with_demand,
        groups=groups,
        current_sort=sort,
        current_status=status,
        current_search=search,
        current_page=page,
        total_pages=total_pages,
        total_all=total_all,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        procured_count=procured_count,
        demand_chart=demand_chart,
    )


def _build_card_groups(items, variant_lookup):
    """Cluster page rows into per-title card dicts (JSON-safe primitives).

    Row contract from get_requests_with_details:
    0 request_id, 1 requester_id, 2 book_title, 3 author, 4 matched_book_id,
    5 request_status, 6 request_date, 7 reviewed_by, 8 review_date,
    9 remarks, 10 full_name, 11 role_name, 12 department.
    """
    from difflib import SequenceMatcher
    from .models import TITLE_FUZZY_RATIO

    page_groups = []  # [{'norm', 'members': [row]}]
    for r in items or []:
        title = r[2] if len(r) > 2 else ''
        norm = normalize_title(title or '')
        target = None
        for g in page_groups:
            if norm and norm == g['norm']:
                target = g
                break
            try:
                if norm and SequenceMatcher(None, norm, g['norm']).ratio() >= TITLE_FUZZY_RATIO:
                    target = g
                    break
            except Exception:
                continue
        if target is None:
            page_groups.append({'norm': norm, 'members': [r]})
        else:
            target['members'].append(r)

    cards = []
    for g in page_groups:
        members = g['members']
        # Canonical display: most common spelling on this page.
        spellings = {}
        for m in members:
            spellings[m[2]] = spellings.get(m[2], 0) + 1
        display = max(spellings.items(), key=lambda kv: (kv[1], -len(kv[0])))[0]
        # Author: most common non-empty value.
        authors = {}
        for m in members:
            a = (m[3] or '').strip()
            if a:
                authors[a] = authors.get(a, 0) + 1
        author = max(authors.items(), key=lambda kv: kv[1])[0] if authors else None

        # Global merged demand when this spelling (or a fuzzy twin) has
        # pending/approved rows; otherwise fall back to page members so
        # rejected-only titles still render a truthful bar.
        global_group = variant_lookup.get(display)
        if global_group is None:
            for variant, grp in variant_lookup.items():
                try:
                    if normalize_title(variant) == g['norm'] or \
                            SequenceMatcher(None, normalize_title(variant), g['norm']).ratio() >= TITLE_FUZZY_RATIO:
                        global_group = grp
                        break
                except Exception:
                    continue
        if global_group is not None:
            student = int(global_group['counts'].get('Student', 0) or 0)
            faculty = int(global_group['counts'].get('Faculty', 0) or 0)
            total = int(global_group['total'] or 0)
            display = global_group['display']
        else:
            student = sum(1 for m in members if len(m) > 11 and m[11] == 'Student')
            faculty = sum(1 for m in members if len(m) > 11 and m[11] == 'Faculty')
            total = len(members)
        other = max(total - student - faculty, 0)
        if total > 0:
            student_pct = round(student / total * 100, 1)
            faculty_pct = round(faculty / total * 100, 1)
            other_pct = round(other / total * 100, 1)
        else:
            student_pct = faculty_pct = other_pct = 0.0

        pending_ids = [m[0] for m in members if len(m) > 5 and m[5] == 'pending_review']
        statuses = sorted({m[5] for m in members if len(m) > 5 and m[5]})
        requesters = []
        for m in members:
            name = m[10] if len(m) > 10 else ''
            role = m[11] if len(m) > 11 else ''
            dept = m[12] if len(m) > 12 else ''
            requesters.append({
                'request_id': m[0], 'name': name, 'role': role,
                'department': dept, 'status': m[5] if len(m) > 5 else '',
                'remarks': m[9] if len(m) > 9 else None,
            })
        dates = [str(m[6]) for m in members if len(m) > 6 and m[6]]
        newest_key = max(dates) if dates else ''
        cards.append({
            'display': display,
            'author': author,
            'total': total,
            'student': student,
            'faculty': faculty,
            'other': other,
            'student_pct': student_pct,
            'faculty_pct': faculty_pct,
            'other_pct': other_pct,
            'both': student > 0 and faculty > 0,
            'pending_ids': pending_ids,
            'pending_count': len(pending_ids),
            'statuses': statuses,
            'requesters': requesters,
            'shown_requesters': requesters[:3],
            'extra_requesters': max(len(requesters) - 3, 0),
            'oldest': min(dates) if dates else '',
            'newest_key': newest_key,
            'members': [
                {'request_id': m[0], 'status': m[5] if len(m) > 5 else '',
                 'name': m[10] if len(m) > 10 else '',
                 'role': m[11] if len(m) > 11 else '',
                 'remarks': m[9] if len(m) > 9 else None}
                for m in members
            ],
        })
    return cards


@requests_bp.route('/librarian/requests/bulk/<action>', methods=['POST'])
@login_required
@librarian_required
def bulk_review(action):
    """Approve / reject every pending request id in one librarian click.

    Form: request_ids = "7,9,12" (capped at 100), remarks optional for
    rejects. Non-pending / missing ids are skipped and reported.
    """
    if action not in ('approve', 'reject'):
        flash('Invalid action.', 'error')
        return redirect(url_for('requests.list_requests'))

    raw = request.form.get('request_ids', '')
    ids = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            rid = int(part)
        except (TypeError, ValueError):
            continue
        if rid > 0 and rid not in ids:
            ids.append(rid)
        if len(ids) >= 100:
            break
    if not ids:
        flash('No requests selected.', 'error')
        return redirect(url_for('requests.list_requests'))

    status = 'approved' if action == 'approve' else 'rejected'
    remarks = request.form.get('remarks', '').strip() or None
    done, skipped = 0, 0
    for rid in ids:
        existing = get_request_by_id(rid)
        if not existing or existing[5] != 'pending_review':
            skipped += 1
            continue
        update_request_status(rid, status, reviewer_id=current_user.id, remarks=remarks)
        if action == 'approve':
            create_procurement(rid)
        try:
            from app.circulation.models import create_notification
            borrower_id = existing[1] if len(existing) > 1 else None
            title = existing[2] if len(existing) > 2 else f'request #{rid}'
            if borrower_id is not None:
                create_notification(
                    borrower_id,
                    f'Your book request for "{title}" was {status}.'
                    + (f' Remarks: {remarks}' if remarks else ''),
                    'request_update',
                    str(rid),
                )
        except Exception:
            pass
        log_activity(current_user.id, f'requests:{action}:{rid}')
        done += 1

    if done:
        flash(f'{done} request(s) {status}.{"" if not skipped else f" {skipped} skipped (already reviewed)."}', 'success')
    else:
        flash('Nothing changed — selected requests were already reviewed.', 'error')
    return redirect(url_for('requests.list_requests'))

@requests_bp.route('/librarian/requests/<int:request_id>/<action>', methods=['POST'])
@login_required
@librarian_required
def review_request(request_id, action):
    if action not in ('approve', 'reject'):
        flash('Invalid action.', 'error')
        return redirect(url_for('requests.list_requests'))

    existing = get_request_by_id(request_id)
    if not existing:
        flash('Request not found.', 'error')
        return redirect(url_for('requests.list_requests'))

    if existing[5] != 'pending_review':
        flash('This request has already been reviewed.', 'error')
        return redirect(url_for('requests.list_requests'))

    status = 'approved' if action == 'approve' else 'rejected'
    remarks = request.form.get('remarks', '').strip() or None
    update_request_status(request_id, status, reviewer_id=current_user.id, remarks=remarks)

    if action == 'approve':
        create_procurement(request_id)

    try:
        from app.circulation.models import create_notification
        borrower_id = existing[1] if len(existing) > 1 else None
        title = existing[2] if len(existing) > 2 else f'request #{request_id}'
        if borrower_id is not None:
            create_notification(
                borrower_id,
                f'Your book request for "{title}" was {status}.'
                + (f' Remarks: {remarks}' if remarks else ''),
                'request_update',
                str(request_id),
            )
    except Exception:
        pass

    log_activity(current_user.id, f'requests:{action}:{request_id}')
    flash(f'Request {status}.', 'success')
    return redirect(url_for('requests.list_requests'))

@requests_bp.route('/user/request-book', methods=['GET', 'POST'])
@login_required

def user_request_book():
    if request.method == 'POST':
        book_title = request.form.get('book-title', '').strip()
        author = request.form.get('author', '').strip() or None

        if not book_title:
            flash('Book title is required.', 'error')
            return redirect(url_for('requests.user_request_book'))

        if len(book_title) > 255:
            flash('Book title is too long (max 255 characters).', 'error')
            return redirect(url_for('requests.user_request_book'))

        if author and len(author) > 150:
            flash('Author name is too long (max 150 characters).', 'error')
            return redirect(url_for('requests.user_request_book'))

        borrower_id = get_borrower_by_user(current_user.id)
        if not borrower_id:
            flash('Only registered borrowers can submit requests.', 'error')
            return redirect(url_for('requests.user_request_book'))

        if check_duplicate_request(borrower_id, book_title):
            flash('You already requested this book.', 'error')
            return redirect(url_for('requests.user_request_book'))

        if check_catalog_exists(book_title) or check_approved_request_exists(book_title):
            flash('Book is already existing in the catalog', 'error')
            return redirect(url_for('requests.user_request_book'))

        new_request_id = create_request(borrower_id, book_title, author)
        try:
            from app.circulation.models import create_notification
            create_notification(
                borrower_id,
                f'Book request for "{book_title}" submitted and pending review.',
                'request_update',
                str(new_request_id),
            )
        except Exception:
            pass
        log_activity(current_user.id, f'requests:create:{new_request_id}')
        flash('Your request has been submitted!', 'success')
        return redirect(url_for('requests.user_request_book'))

    borrower_id = get_borrower_by_user(current_user.id)
    my_requests = get_requests_by_borrower(borrower_id) if borrower_id else []
    return render_template('requests/user_request_book.html', my_requests=my_requests)