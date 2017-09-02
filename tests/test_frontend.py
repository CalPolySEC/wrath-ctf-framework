# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from ctf import core, create_app, ext, frontend, models, setup
from datetime import datetime, timedelta
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
        setup.build_challenges()

    return app


@pytest.fixture(scope='function')
def client(app):
    with app.test_client() as cli:
        yield cli


@pytest.fixture(scope='function')
def team_data(app):
    with app.app_context():
        teams = [models.Team(name='team{0}'.format(i)) for i in range(10)]
        for team in teams:
            ext.db.session.add(team)
        ext.db.session.commit()

        # This expects your test config to have 2 challenges
        challenges = models.Challenge.query.all()
        for i, team in enumerate(teams):
            if i % 2 == 1:
                # Directly create a Solve record with a custom datetime, so
                # that we get a deterministic order for team rankings
                solve = models.Solve(
                    team_id=team.id,
                    challenge_id=challenges[0].id,
                    earned_on=(datetime.now() - timedelta(seconds=i)),
                )
                ext.db.session.add(solve)
            if i % 4 <= 1:
                solve = models.Solve(
                    team_id=team.id,
                    challenge_id=challenges[1].id,
                    earned_on=(datetime.now() - timedelta(seconds=i)),
                )
                ext.db.session.add(solve)
        ext.db.session.commit()


@pytest.fixture
def user_without_team(app, client):
    username = 'harry'
    password = 'expecto.patronum⚡'
    with app.app_context():
        user = core.create_user(username, password)
        key = core.create_session_key(user)

    with client.session_transaction() as sess:
        sess['key'] = key


@pytest.fixture
def user(app, user_without_team):
    with app.app_context():
        user = models.User.query.filter(models.User.name == 'harry').first()
        team = models.Team(name='Gryffindor')
        user.team = team
        ext.db.session.add(team)
        ext.db.session.commit()


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


def test_create_existing_user(app, client, user_without_team):
    """Assert that we can't create (case-insensitive) duplicate users."""
    form_data = {'username': 'HaRrY', 'password': 'expecto.patronum⚡'}
    rv = client.post('/register/', data=form_data)
    assert rv.status_code == 409
    assert b'That username is taken.' in rv.data


def test_login(app, client, user_without_team):
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


@pytest.mark.parametrize('username,password', [
    ('hermione', 'expecto.patronum⚡'),
    ('harry', 'avada.kedavra🐍'),
])
def test_login_incorrect(client, username, password):
    """Check logging in with bad creds."""
    form_data = {'username': username, 'password': password}
    rv = client.post('/login/', data=form_data)
    assert rv.status_code == 403
    assert b'Incorrect username or password.' in rv.data


def test_home(client, team_data):
    rv = client.get('/')
    assert rv.status_code == 200

    scoreboard = []
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
    for i, row in enumerate(html.find_all('tr')):
        rank, team, score = row.find_all('td')
        assert rank.text == str(i + 1)
        scoreboard.append((team.text, int(score.text)))

    assert scoreboard == [
        ('team9', 40),
        ('team5', 40),
        ('team1', 40),
        ('team7', 30),
        ('team3', 30),
        ('team8', 10),
        ('team4', 10),
        ('team0', 10),
        ('team2', 0),
        ('team6', 0),
    ]


def test_challenge_page(client, user):
    rv = client.get('/challenges/')
    assert rv.status_code == 200

    assert b'Test Crypto' in rv.data
    assert b'Test Web' in rv.data
    assert b'Test Web Dep' not in rv.data


def test_challenge_page_unauthed(client):
    rv = client.get('/challenges/')
    assert rv.status_code == 303
    assert rv.headers['Location'].endswith('/login/?next=%2Fchallenges%2F')


def test_challenge_page_without_team(client, user_without_team):
    rv = client.get('/challenges/')
    assert rv.status_code == 303
    assert rv.headers['Location'].endswith('/')

    assert b'You must be part of a team.' in client.get('/').data


def test_post_fleg(client, user):
    rv = client.post('/challenges/', data={'fleg': 'test_fleg'})
    assert rv.status_code == 200
    assert b'Correct! You have earned 30 points for your team.' in rv.data

    # No double submit
    rv = client.post('/challenges/', data={'fleg': 'test_fleg'})
    assert rv.status_code == 200
    assert b"You&#39;ve already entered that flag." in rv.data


def test_post_fleg_incorrect(client, user):
    rv = client.post('/challenges/', data={'fleg': 'wrong_fleg'})
    assert rv.status_code == 200
    assert b'Nope.' in rv.data


def test_fleg_snoop(client, user):
    rv = client.post('/challenges/', data={'fleg': 'V375BrzPaT'})
    assert rv.status_code == 303
    assert rv.headers['Location'] == \
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ'


def test_url_snoop(client, user):
    rv = client.get('/passwords.zip')
    assert rv.status_code == 303
    assert rv.headers['Location'] == \
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
