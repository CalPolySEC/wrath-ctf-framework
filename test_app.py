from ctf_app import app, db, Team
import pytest
import tempfile

@pytest.fixture
def client():
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'my secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % tempfile.mktemp()
    db.create_all()
    return app.test_client()


def test_static_pages(client):
    for url in ('/login', '/about', '/contact'):
        rv = client.get(url)
        assert rv.status_code == 200


def test_team_404(client):
    for url in ('/teams/1', '/teams/0', '/teams/-1', '/teams/asdf'):
        rv = client.get(url)
        assert rv.status_code == 404


def test_new_team(client):
    rv = client.post('/teams', data={
        'name': 'Sgt. Pepper\'s Lonely Hearts Club Band'
    })
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/teams/1'

    rv = client.get('/teams/1')
    assert b'Team successfully created.' in rv.data
    assert b'<h1>Sgt. Pepper&#39;s Lonely Hearts Club Band</h1>' in rv.data


def test_new_team_missing_name(client):
    rv = client.post('/teams')
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/login'
    assert b'You must supply a team name.' in client.get('/').data


def test_new_team_duplicate(client):
    rv = client.post('/teams', data={'name': 'Some Team Name'})
    rv = client.post('/teams', data={'name': 'sOmE tEaM nAme'})
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/login'
    assert b'That team name is taken.' in client.get('/').data


def test_login(client):
    def assert_bad_login(data, message):
        rv = client.post('/auth_team', data=data)
        assert rv.status_code == 303
        assert rv.headers['Location'] == 'http://localhost/login'
        assert message in client.get('/').data

    assert_bad_login({}, b'No team exists with that name.')
    assert_bad_login({'username': 'abc'}, b'No team exists with that name.')
    assert_bad_login({'username': 'abc', 'password': 'abc'},
                     b'No team exists with that name.')

    client.post('/teams', data={'name': 'Abc'})
    assert_bad_login({'name': 'ABC', 'password': 'abc'},
                     b'Incorrect team password.')

    password = Team.query.filter_by(id=1).first().password
    rv = client.post('/auth_team', data={'name': 'ABC', 'password': password})
    assert rv.headers['Location'] == 'http://localhost/teams/1'


def test_logout(client):
    rv = client.get('/logout')
