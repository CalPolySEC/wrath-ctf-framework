# -*- coding: utf-8 -*-
from ctf import create_app, ext, frontend
import fakeredis
import pytest
import os


@pytest.fixture
def app(monkeypatch):
    os.environ["CTF_CONFIG"] = "tests/configs/good.json"
    app = create_app(test=True)
    app.redis = fakeredis.FakeRedis()
    app.secret_key = 'my secret key'
    app.debug = True
    # We aren't trying to test CSRF here
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    ext.csrf.exempt(frontend.bp)
    monkeypatch.setattr(frontend, 'validate_csrf', lambda d: d == 'token')
    return app


def test_user_auth(app):
    with app.test_client() as client:
        def create_user(username, password, status, message=None):
            rv = client.post('/register/', data={
                'username': username,
                'password': password,
            })
            if message is not None:
                assert message in rv.data
            assert rv.status_code == status
            return rv

        def login(username, password, status, message=None):
            rv = client.post('/login/', data={
                'username': username,
                'password': password,
            })
            if message is not None:
                assert message in rv.data
            assert rv.status_code == status
            return rv

        # Should not be authed
        rv = client.get('/team/')
        assert rv.status_code == 303
        assert '/login/' in rv.headers['Location']
        rv = client.get('/login/')
        assert b'You must be logged in to do that.' in rv.data

        # Form validation
        rv = create_user('', '', 400)
        assert b'Csrf Token: CSRF token missing' not in rv.data
        assert b'Username: This field is required.' in rv.data
        assert b'Password: This field is required.' in rv.data

        # User creaton
        rv = create_user('harry', 'expecto.patronum⚡', 303)
        assert rv.headers['Location'] == 'http://localhost/'
        # Should be logged in now
        assert client.get('/team/').status_code == 200

        # Logout
        rv = client.get('/logout/?token=token')
        assert rv.status_code == 303
        # Double check
        rv = client.get('/team/')
        assert rv.status_code == 303
        assert '/login/' in rv.headers['Location']
        rv = client.get('/login/')
        assert b'You must be logged in to do that.' in rv.data

        # Duplicate users
        create_user('harry', 'badpw', 409, b'That username is taken.')
        create_user('hArRy', 'badpw', 409, b'That username is taken.')

        # Login
        login('abc', 'badpw', 403, b'Incorrect username or password.')
        login('harry', 'badpw', 403, b'Incorrect username or password.')
        login('harry', 'harry', 403, b'Incorrect username or password.')

        login('harry', 'expecto.patronum⚡', 303)  # This will set a token
        # Should be logged in again
        assert client.get('/team/').status_code == 200
