from app.database import db


def get_resources(active_only=True):
    if active_only:
        return db.fetch_all(
            '''SELECT resource_id, title, provider, url, description, is_active, date_added
               FROM online_resources WHERE is_active = TRUE ORDER BY title'''
        )
    return db.fetch_all(
        '''SELECT resource_id, title, provider, url, description, is_active, date_added
           FROM online_resources ORDER BY is_active DESC, title'''
    )


def get_resource_by_id(resource_id):
    return db.fetch_one(
        '''SELECT resource_id, title, provider, url, description, is_active, date_added
           FROM online_resources WHERE resource_id = %s''',
        (resource_id,)
    )


def create_resource(title, url, provider=None, description=None, added_by=None):
    return db.execute(
        '''INSERT INTO online_resources (title, url, provider, description, added_by)
           VALUES (%s, %s, %s, %s, %s)''',
        (title, url, provider, description, added_by)
    )


def set_resource_active(resource_id, active):
    return db.execute(
        'UPDATE online_resources SET is_active = %s WHERE resource_id = %s',
        (bool(active), resource_id)
    )


def log_access(resource_id, user_id):
    return db.execute(
        'INSERT INTO online_resource_access (resource_id, user_id) VALUES (%s, %s)',
        (resource_id, user_id)
    )


def count_resources(active_only=True):
    if active_only:
        row = db.fetch_one(
            'SELECT COUNT(*) FROM online_resources WHERE is_active = TRUE')
    else:
        row = db.fetch_one('SELECT COUNT(*) FROM online_resources')
    return row[0] if row else 0


def resource_usage(start_date=None, end_date=None, limit=5):
    """Top online resources by recorded visits: [(title, provider, accesses)]."""
    parts, params = [], []
    if start_date is not None:
        parts.append('a.accessed_at >= %s')
        params.append(start_date)
    if end_date is not None:
        parts.append('a.accessed_at <= %s')
        params.append(end_date)
    date_cond = ' AND ' + ' AND '.join(parts) if parts else ''
    params.append(limit)
    return db.fetch_all(
        '''SELECT r.title, r.provider, COUNT(a.access_id)
           FROM online_resources r
           LEFT JOIN online_resource_access a
               ON a.resource_id = r.resource_id{}
           WHERE r.is_active = TRUE
           GROUP BY r.resource_id, r.title, r.provider
           HAVING COUNT(a.access_id) > 0
           ORDER BY 3 DESC LIMIT %s'''.format(date_cond),
        tuple(params)
    )


def count_accesses(start_date=None, end_date=None):
    parts, params = [], []
    if start_date is not None:
        parts.append('accessed_at >= %s')
        params.append(start_date)
    if end_date is not None:
        parts.append('accessed_at <= %s')
        params.append(end_date)
    where = 'WHERE ' + ' AND '.join(parts) if parts else ''
    row = db.fetch_one(
        'SELECT COUNT(*) FROM online_resource_access {}'.format(where),
        tuple(params) if params else None
    )
    return row[0] if row else 0
