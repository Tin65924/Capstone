"""Protect existing duplicate records during schema initialization."""
from unittest.mock import MagicMock

import pytest

from app import database


@pytest.mark.parametrize('index_name', [
    'uq_procurement_log_request_id',
    'uq_inventory_status_accession_id',
])
def test_required_index_failure_stops_startup_without_deleting_rows(app, index_name):
    pool = MagicMock()
    conn = pool.getconn.return_value
    cursor = conn.cursor.return_value.__enter__.return_value

    def execute(statement, *args):
        if index_name in statement:
            raise RuntimeError('duplicate key')

    cursor.execute.side_effect = execute
    original = database.db._pool
    database.db._pool = pool
    try:
        with pytest.raises(database.RequiredSchemaMigrationError):
            database.run_schema(app)
    finally:
        database.db._pool = original
    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert not any('DELETE FROM procurement_log older' in sql for sql in statements)
    assert not any('DELETE FROM inventory_status older' in sql for sql in statements)
    pool.putconn.assert_called_once_with(conn)
