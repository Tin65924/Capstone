from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__, template_folder='../templates/analytics')


def schedule_prewarm(app):
    """Warm the dashboard cache for common filter sets in a boot thread.

    A first-ever filter set has no cached row to serve stale, so the first
    request for it blocks on the full ~40-query recompute (~10s on Neon).
    After startup, compute the default landing ranges ('all', 'year',
    'month') plus every single-department 'year' variant (the department
    filter's options), so prod users only ever pay for filter combinations
    never warmed. Best-effort: failures log and stop, never raise.
    """
    if app.config.get('TESTING') or app.config.get('SKIP_SCHEMA_SYNC'):
        return
    import threading
    from . import routes as _routes

    def _prewarm():
        try:
            with app.app_context():
                warmed = {}
                for preset in ('all', 'year', 'month'):
                    start_date, end_date = _routes.resolve_dates(preset, '', '')
                    warmed[preset] = _routes.compute_dashboard(start_date, end_date, None)
                    app.logger.info('analytics prewarm: %s done', preset)
                # Single-department variants reuse the warmed 'year' payload's
                # department list (same source the filter dropdown uses).
                usage = (warmed.get('year') or {}).get('usage') or {}
                for row in usage.get('by_department_all') or []:
                    name = (row[0] or '').strip()
                    if not name:
                        continue
                    start_date, end_date = _routes.resolve_dates('year', '', '')
                    _routes.compute_dashboard(start_date, end_date, [name])
                    app.logger.info('analytics prewarm: year/%s done', name)
        except Exception as e:
            try:
                app.logger.warning('analytics prewarm stopped: %s', e)
            except Exception:
                pass

    threading.Thread(target=_prewarm, name='analytics-prewarm', daemon=True).start()

from . import routes

