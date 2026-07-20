import os
import psycopg2
from psycopg2 import pool
from flask import current_app, g

class Database:
    def __init__(self, app=None):
        self._pool = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        dsn = app.config['DATABASE_URL']
        self._pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn
        )
        app.teardown_appcontext(self.close_connection)

    def get_connection(self):
        if 'db_conn' not in g:
            g.db_conn = self._pool.getconn()
        return g.db_conn

    def close_connection(self, exc=None):
        conn = g.pop('db_conn', None)
        if conn is not None:
            self._pool.putconn(conn)

    def execute(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
        except Exception as e:
            conn.rollback()
            raise e

    def fetch_one(self, query, params=None):
        rows = self.execute(query, params)
        return rows[0] if rows else None

    def fetch_all(self, query, params=None):
        return self.execute(query, params)

db = Database()


def run_schema(app):
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.isfile(schema_path):
        app.logger.warning('schema.sql not found — skipping schema initialization')
        return
    conn = db._pool.getconn()
    try:
        with conn.cursor() as cur:
            with open(schema_path, 'r') as f:
                cur.execute(f.read())
        conn.commit()
        app.logger.info('Database schema initialized successfully.')
    except Exception as e:
        conn.rollback()
        app.logger.warning('Schema initialization skipped (may already exist): %s', e)
    finally:
        db._pool.putconn(conn)


def init_db(app):
    db.init_app(app)
    run_schema(app)
