"""Exercise CSRF enforcement with protection enabled, unlike route fixtures."""


def test_mutation_without_token_is_rejected(app, student_client):
    app.config['WTF_CSRF_ENABLED'] = True
    assert student_client.post('/logout').status_code == 400


def test_logout_accepts_session_bound_form_token(app, student_client):
    app.config['WTF_CSRF_ENABLED'] = True
    student_client.get('/user/profile')
    with student_client.session_transaction() as session:
        token = session['_csrf_token']
    assert student_client.post('/logout', data={'csrf_token': token}).status_code == 302


def test_logout_accepts_session_bound_header_token(app, student_client):
    app.config['WTF_CSRF_ENABLED'] = True
    student_client.get('/user/profile')
    with student_client.session_transaction() as session:
        token = session['_csrf_token']
    assert student_client.post('/logout', headers={'X-CSRFToken': token}).status_code == 302
