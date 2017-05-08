# -*- coding: utf-8 -*-
from ctf import core, create_app, ext, frontend
import fakeredis
import flask
import pytest
import os


@pytest.fixture(scope='function')
def app(monkeypatch):
    os.environ["CTF_CONFIG"] = "tests/configs/good.json"
    app = create_app()
    app.redis = fakeredis.FakeRedis()
    app.secret_key = 'my secret key'
    app.debug = True

    # In-memory database only
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    # We aren't trying to test CSRF here
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    ext.csrf.exempt(frontend.bp)
    # This will let us still test flask_wtf.csrf.validate_csrf from /logout/
    monkeypatch.setattr(frontend, 'validate_csrf', lambda d: d == 'token')

    with app.app_context():
        ext.db.create_all()

    return app


@pytest.fixture(scope='function')
def client(app):
    with app.test_client() as cli:
        yield cli


@pytest.fixture
def user(app, client):
    username = 'harry'
    password = 'expecto.patronum⚡'
    with app.app_context():
        user = core.create_user(username, password)
        key = core.create_session_key(user)

    with client.session_transaction() as sess:
        sess['key'] = key


def test_create_user(app, client):
    """Assert that we can create a user."""
    form_data = {'username': 'harry', 'password': 'expecto.patronum⚡'}
    rv = client.post('/register/', data=form_data)
    assert rv.status_code == 303
    assert rv.location == 'http://localhost/'

    with app.app_context():
        user = core.user_for_token(flask.session['key'])
        assert user.name == 'harry'


@pytest.mark.parametrize('username,password', [
    (None, None),
    (None, ''),
    ('', None),
    ('', ''),
    ('harry', ''),
    ('', 'expecto.patronum⚡'),
])
def test_create_user_invalid(client, username, password):
    """Assert that our form validates bad input."""
    form_data = {}
    if username is not None:
        form_data['username'] = username
    if password is not None:
        form_data['password'] = password

    rv = client.post('/register/', data=form_data)
    assert rv.status_code == 400

    if not username:
        assert b'Username: This field is required.' in rv.data
    if not password:
        assert b'Password: This field is required.' in rv.data


def test_create_existing_user(app, client, user):
    """Assert that we can't create (case-insensitive) duplicate users."""
    form_data = {'username': 'HaRrY', 'password': 'expecto.patronum⚡'}
    rv = client.post('/register/', data=form_data)
    assert rv.status_code == 409
    assert b'That username is taken.' in rv.data


def test_login(app, client, user):
    """Assert that we can log in."""
    form_data = {'username': 'harry', 'password': 'expecto.patronum⚡'}
    rv = client.post('/login/', data=form_data)
    assert rv.status_code == 303
    assert rv.location == 'http://localhost/'

    with app.app_context():
        user = core.user_for_token(flask.session['key'])
        assert user.name == 'harry'


@pytest.mark.parametrize('username,password', [
    (None, None),
    (None, ''),
    ('', None),
    ('', ''),
    ('harry', ''),
    ('', 'expecto.patronum⚡'),
])
def test_login_invalid(client, username, password):
    """Assert that our login form validates bad input."""
    form_data = {}
    if username is not None:
        form_data['username'] = username
    if password is not None:
        form_data['password'] = password

    rv = client.post('/login/', data=form_data)
    assert rv.status_code == 400

    if not username:
        assert b'Username: This field is required.' in rv.data
    if not password:
        assert b'Password: This field is required.' in rv.data
