from ctf import core, create_app
from ctf.ext import db
from ctf.frontend import is_safe_url
import fakeredis
import os
import pytest
import tempfile


@pytest.fixture
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///%s' % tempfile.mktemp()
    app = create_app()
    app.redis = fakeredis.FakeRedis()
    app.secret_key = 'my secret key'
    app.debug = True
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        return client


def get_token(client):
    rv = client.get('/login/')
    token = rv.data.split(b'name="csrf_token" type="hidden" value="', 1)[1]
    return token.split(b'"', 1)[0].decode('utf-8')


def auth(client):
    with client.application.test_request_context('/'):
        db.create_all()
        user = core.create_user('Abc', 'def')
        db.session.add(user)
        db.session.commit()
    data = {
        'username': 'abc',
        'password': 'def',
        'csrf_token': get_token(client),
    }
    assert client.post('/login/', data=data).status_code == 303


def test_is_safe_url(app):
    with app.test_request_context('/url'):
        assert is_safe_url('')
        assert is_safe_url('/')
        assert is_safe_url('/abc')
        assert not is_safe_url('/url')
        assert not is_safe_url('//example.com')
        assert not is_safe_url('http://abc')
        assert not is_safe_url('http://example.com')
        assert not is_safe_url('http://example.com/abc')
        assert not is_safe_url('http://localhost:1234/abc')
        assert not is_safe_url('http://localhost/')
        assert not is_safe_url('http://localhost')
        assert not is_safe_url('ftp://localhost/abc')
        assert not is_safe_url('http://localhost/abc')


def test_error(app):
    @app.route('/internal')
    def cause_a_problem():
        1 / 0

    @app.route('/post', methods=['POST'])
    def post_only():
        return 'OK\n'

    app.debug = False

    with app.test_client() as client:
        for url, code in (('/asdf', 404), ('/post', 405), ('/internal', 500)):
            rv = client.get(url)
            assert b'https://http.cat/' + str(code).encode() in rv.data
            assert rv.status_code == code


def test_static_pages(client):
    rv = client.get('/login/')
    assert rv.status_code == 200


def test_team_404(client):
    for url in ('/teams/1/', '/teams/0/', '/teams/-1/', '/teams/a',
                '/teams/a/'):
        rv = client.get(url)
        assert rv.status_code == 404


def test_bad_csrf(client):
    client.get('/register/')

    rv = client.post('/register/', data={'name': 'myname'})
    assert rv.status_code == 400

    rv = client.post('/register/', data={'name': 'myname', 'csrf_token': 'x'})
    assert rv.status_code == 400


def test_login(client):
    token = get_token(client)

    def assert_login_status(data, code):
        data['csrf_token'] = token
        rv = client.post('/login/', data=data)
        assert rv.status_code == code
        return rv

    assert_login_status({}, 200)
    assert_login_status({'username': 'abc'}, 200)
    assert_login_status({'username': 'abc', 'password': 'abc'}, 403)

    auth(client)
    rv = assert_login_status({'username': 'ABC', 'password': 'def'}, 303)
    assert rv.headers['Location'] == 'http://localhost/'


def test_logout_unauthed(client):
    rv = client.get('/logout/')
    assert rv.status_code == 303
    assert rv.headers['Location'] == ('http://localhost/login/'
                                      '?next=%2Flogout%2F')


def test_logout_bad_token(client):
    auth(client)
    rv = client.get('/logout/')
    assert rv.status_code == 400
    assert b'Missing or incorrect CSRF token.' in rv.data

    rv = client.get('/logout/?token=abc')
    assert rv.status_code == 400
    assert b'Missing or incorrect CSRF token.' in rv.data


def test_logout(client):
    auth(client)
    token = get_token(client)

    rv = client.get('/logout/?token=%s' % token)
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/'

    assert get_token(client) != token
