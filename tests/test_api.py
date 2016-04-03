from ctf.app import create_app
import json
import os
import pytest
import tempfile


@pytest.fixture
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///%s' % tempfile.mktemp()
    app = create_app()
    app.secret_key = 'my secret key'
    app.debug = True
    return app


def api_req(fn, url, token, data=None):
    headers = {}
    if token:
        headers['X-Session-Key'] = token

    if data:
        headers['Content-Type'] = 'application/json'
        rv = fn(url, data=json.dumps(data), headers=headers)
    else:
        rv = fn(url, headers=headers)
    data = json.loads(rv.data.decode('utf-8'))
    return data, rv.status_code


def test_user_auth(app):
    with app.test_client() as client:
        def create_user(username, password, status, message=None):
            data, status = api_req(client.post, '/api/users/', None, {
                'username': username,
                'password': password,
            })
            assert status == status
            if message:
                assert data['message'] == message
            return data

        def login(username, password, status, message=None):
            data, status = api_req(client.post, '/api/sessions/', None, {
                'username': username,
                'password': password,
            })
            assert status == status
            if message:
                assert data['message'] == message
            return data

        # Input checking
        data, status = api_req(client.post, '/api/users/', None, {})
        assert status == 400
        assert data['message'] == 'Missing JSON value \'username\'.'

        create_user(1, '', 400, 'Expected string for \'username\'.')

        # User creation
        create_user('', '', 400, 'You must supply a username and password.')

        data = create_user('test', 'test', 201)
        assert 'key' in data

        create_user('test', 'badpw', 400, 'That username is taken.')

        # Login
        login('abc', 'badpw', 403, 'Incorrect username or password.')
        login('test', 'badpw', 403, 'Incorrect username or password.')

        data = login('test', 'test', 201)
        key = data['key']

        # Simple auth checking
        for k in (None, '', 'bad.sig', 'fake.TPRM-X0i3azi4DyIqjQy_8jTbHo'):
            data, status = api_req(client.get, '/api/users/me', k)
            assert status == 403
            assert data['message'] == 'A valid X-Session-Key header is required.'


        data, status = api_req(client.get, '/api/users/me', key)
        assert status == 200
