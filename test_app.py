from ctf_app import app, db, Team, Flag, Category
import pytest
import tempfile

@pytest.fixture
def client():
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'my secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % tempfile.mktemp()
    db.create_all()
    return app.test_client()


def auth(client):
    team = Team(name='Abc', password='def')
    db.session.add(team)
    db.session.commit()
    client.post('/auth_team', data={'name': 'abc', 'password': 'def'})


def test_error(client):
    @app.route('/internal')
    def cause_a_problem():
        1 / 0

    app.config['DEBUG'] = False

    for url, code in (('/asdf', 404), ('/teams', 405), ('/internal', 500)):
        rv = client.get(url)
        assert b'https://http.cat/%d' % code in rv.data
        assert rv.status_code == code


def test_static_pages(client):
    for url in ('/login/', '/about/', '/contact/'):
        rv = client.get(url)
        assert rv.status_code == 200


def test_team_404(client):
    for url in ('/teams/1/', '/teams/0/', '/teams/-1/', '/teams/a',
                '/teams/a/'):
        rv = client.get(url)
        assert rv.status_code == 404


def test_new_team(client):
    rv = client.post('/teams', data={
        'name': 'Sgt. Pepper\'s Lonely Hearts Club Band'
    })
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/teams/1/'

    rv = client.get('/teams/1/')
    assert b'Team successfully created.' in rv.data
    assert b'>Sgt. Pepper&#39;s Lonely Hearts Club Band<' in rv.data


def test_new_team_missing_name(client):
    rv = client.post('/teams')
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/login/'
    assert b'You must supply a team name.' in client.get('/').data


def test_new_team_duplicate(client):
    rv = client.post('/teams', data={'name': 'Some Team Name'})
    rv = client.post('/teams', data={'name': 'sOmE tEaM nAme'})
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/login/'
    assert b'That team name is taken.' in client.get('/').data


def test_login(client):
    def assert_bad_login(data, message):
        rv = client.post('/auth_team', data=data)
        assert rv.status_code == 303
        assert rv.headers['Location'] == 'http://localhost/login/'
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
    assert rv.headers['Location'] == 'http://localhost/teams/1/'


def test_logout_unauthed(client):
    rv = client.get('/logout')
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/login/'


def test_logout_bad_token(client):
    auth(client)
    rv = client.get('/logout')
    assert rv.status_code == 403
    rv = client.get('/logout?token=abc')
    assert rv.status_code == 403


def test_logout(client):
    auth(client)

    rv = client.get('/')
    token = rv.data.split(b'/logout?token=', 1)[1]
    token = token.split(b'"', 1)[0].decode('utf-8')

    rv = client.get('/logout?token=%s' % token)
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/'


def test_submit_page(client):
    rv = client.get('/submit/')
    assert rv.status_code == 303
    assert rv.headers['Location'] == 'http://localhost/login/'

    auth(client)

    rv = client.get('/submit/')
    assert rv.status_code == 200


def test_flag_submission(client):
    def assert_flag(flag, msg):
        rv = client.post('/flags', data={'flag': flag})
        assert rv.status_code == 303
        assert rv.headers['Location'] == 'http://localhost/submit/'
        assert msg in client.get('/').data

    # SHA-256 of "fleg"
    sha = 'cc78431eedada5a45ac10eae0838b5f84e023758e9baec5ed1f58ffa3722527a'
    cat = Category(name='Bandit')
    fleg = Flag(hash=sha, points=10, category=cat, level=0)
    db.session.add(cat)
    db.session.add(fleg)
    db.session.commit()

    rv = client.get('/')
    assert b'<td>10</td>' not in rv.data

    auth(client)

    assert_flag('abc', b'Sorry, the flag you entered is not correct.')
    assert_flag('fleg', b'Correct! You have earned 10 points for your team.')
    assert_flag('fleg', b'You&#39;ve already entered that flag.')

    rv = client.get('/')
    assert b'<td>10</td>' in rv.data
