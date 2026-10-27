"""Tests for the optional Student and Faculty member tutorial API."""


def test_ebook_example_uses_real_title(student_client, mock_db):
    mock_db['fetch_one'].return_value = (15, 'A & B')
    response = student_client.get('/tutorials/example/ebook')
    assert response.status_code == 200
    assert response.json['book_url'] == '/book/15'
    assert 'field=title' in response.json['catalog_url']
    assert mock_db['fetch_one'].call_args.args[1] == (True, True, '1')
    mock_db['execute'].assert_not_called()


def test_physical_example_empty(student_client, mock_db):
    response = student_client.get('/tutorials/example/borrow')
    assert response.status_code == 404
    mock_db['execute'].assert_not_called()


def test_physical_example_requires_available_copy_not_borrowed_by_member(student_client, mock_db):
    mock_db['fetch_one'].return_value = (8, 'Example')
    response = student_client.get('/tutorials/example/borrow')
    assert response.status_code == 200
    query, params = mock_db['fetch_one'].call_args.args
    assert 'accession_log' in query
    assert 'br.user_id = %s' in query
    assert params == (False, False, '1')


def test_tutorial_rejects_invalid_progress(student_client, mock_db):
    response = student_client.post('/tutorials/progress', json={'status': 'started'})
    assert response.status_code == 400
    mock_db['execute'].assert_not_called()


def test_student_tutorial_status_is_available(student_client, mock_db):
    mock_db['fetch_one'].return_value = ('dismissed',)

    response = student_client.get('/tutorials/status')

    assert response.status_code == 200
    assert response.get_json() == {
        'available': True,
        'status': 'dismissed',
        'version': 1,
    }
    assert 'FROM tutorial_progress' in mock_db['fetch_one'].call_args.args[0]


def test_student_tutorial_progress_is_saved(student_client, mock_db):
    response = student_client.post('/tutorials/progress', json={'status': 'completed'})

    assert response.status_code == 200
    assert response.get_json() == {'status': 'completed'}
    query, params = mock_db['execute'].call_args.args
    assert 'INSERT INTO tutorial_progress' in query
    assert params == ('1', 'member-basics', 1, 'completed')


def test_librarian_tutorial_api_is_not_available(librarian_client, mock_db):
    response = librarian_client.get('/tutorials/status')

    assert response.status_code == 200
    assert response.get_json() == {'available': False}
    mock_db['fetch_one'].assert_not_called()


def test_profile_includes_member_tutorial_launcher(student_client, mock_db):
    mock_db['fetch_one'].return_value = (1, 'student@mcst.edu.ph', 'Student', 'Test Student')

    response = student_client.get('/user/profile')

    assert response.status_code == 200
    assert b'Help / Tutorials' in response.data
    assert b'Start tutorial' in response.data
    assert b'Not now' in response.data
    assert b'data-guide="catalog"' in response.data
    assert b'data-guide="borrow"' in response.data
    assert b'data-guide="ebook"' in response.data
    assert b'aria-live="polite"' in response.data
    assert b'data-tutorial-invite' in response.data


def test_history_includes_tutorial_targets(student_client, mock_db):
    response = student_client.get('/user/history?tab=reservations')

    assert response.status_code == 200
    assert b'data-tour="history-tabs"' in response.data
    assert b'data-tour="history-reservations"' in response.data
    assert b'Help / Tutorials' in response.data


def test_catalog_tutorial_has_search_and_responsive_filters(student_client):
    response = student_client.get('/catalog')
    assert response.status_code == 200
    assert b'data-tour="catalog-search"' in response.data
    assert response.data.count(b'data-tour="catalog-filters"') == 2
    assert b'data-tour="catalog-results"' in response.data
