from ctf.app import create_app
import json
import os
import pytest
import tempfile


@pytest.fixture
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///%s' % tempfile.mktemp()
    app = create_app()
    app.debug = True
    return app


def api_req(fn, url, token, data=None):
    headers = {}
    if token:
        headers['X-Session-Token'] = token
    if data:
        headers['Content-Type'] = 'application/json'
        rv = fn(url, data=json.dumps(data), headers=headers)
    else:
        rv = fn(url, headers=headers)
    return rv


def assert_api_err(resp, status, message):
    assert resp.status_code == status
    data = json.loads(resp.data.decode('utf-8'))
    assert 'message' in data
    assert data['message'] == message


def test_user_auth(app):
    with app.test_client() as client:
        def create_user(username, password):
            return api_req(client.post, '/api/users/', None, {
                'username': username,
                'password': password,
            })

        def login(username, password):
            return api_req(client.post, '/api/sessions/', None, {
                'username': username,
                'password': password,
            })

        # Input checking
        rv = api_req(client.post, '/api/users/', None, {})
        assert_api_err(rv, 400, 'Missing JSON value \'username\'.')

        rv = create_user(1, '')
        assert_api_err(rv, 400, 'Expected string for \'username\'.')

        # User creation
        rv = create_user('', '')
        assert_api_err(rv, 400, 'You must supply a username and password.')

        rv = create_user('test', 'test')
        assert rv.status_code == 201

        rv = create_user('test', 'badpw')
        assert_api_err(rv, 400, 'That username is taken.')

        # Login
        rv = login('abc', 'badpw')
        assert_api_err(rv, 403, 'Incorrect username or password.')

        rv = login('test', 'badpw')
        assert_api_err(rv, 403, 'Incorrect username or password.')

        rv = login('test', 'test')
        assert rv.status_code == 201
