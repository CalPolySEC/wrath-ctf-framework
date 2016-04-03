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


def api_req(fn, url, token=None, data=None):
    headers = {}
    if token:
        headers['X-Session-Key'] = token

    if data:
        headers['Content-Type'] = 'application/json'
        rv = fn(url, data=json.dumps(data), headers=headers)
    else:
        rv = fn(url, headers=headers)
    if rv.data:
        data = json.loads(rv.data.decode('utf-8'))
    else:
        data = None
    return data, rv.status_code


def auth(client):
    data, status = api_req(client.post, '/api/users/', None, {
        'username': 'test',
        'password': 'test',
    })
    assert status == 201
    return data['key']


def test_user_auth(app):
    with app.test_client() as client:
        def create_user(username, password, status, message=None):
            data, code = api_req(client.post, '/api/users/', None, {
                'username': username,
                'password': password,
            })
            assert code == status
            if message:
                assert data['message'] == message
            return data

        def login(username, password, status, message=None):
            data, code = api_req(client.post, '/api/sessions/', None, {
                'username': username,
                'password': password,
            })
            assert code == status
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

        create_user('test', 'badpw', 409, 'That username is taken.')

        # Login
        login('abc', 'badpw', 403, 'Incorrect username or password.')
        login('test', 'badpw', 403, 'Incorrect username or password.')

        data = login('test', 'test', 201)
        key = data['key']

        # Simple auth checking
        for k in (None, '', 'bad.sig', 'fake.TPRM-X0i3azi4DyIqjQy_8jTbHo'):
            data, status = api_req(client.get, '/api/user', k)
            assert status == 403
            assert data['message'] == ('A valid X-Session-Key header '
                                       'is required.')

        data, status = api_req(client.get, '/api/user', key)
        assert status == 200


def test_teams(app):
    def team_req(fn, id=None, name=None, key=None, status=None, message=None):
        url = '/api/teams/'
        if id is not None:
            url += str(id)
        data, code = api_req(fn, url, key, {'name': name})
        assert code == status
        if message:
            assert data['message'] == message
        return data

    with app.test_client() as client:
        key = auth(client)

        # Check that user is null
        data, status = api_req(client.get, '/api/user', key)
        assert status == 200
        assert data['team'] is None

        # Create a team
        team_req(client.post, None, 'PPP', key, 201)
        for name in ('PPP', 'abc'):
            team_req(client.post, None, name, key, 409,
                     'You are already a member of a team.')

        # Get user team
        data, status = api_req(client.get, '/api/user', key)
        assert status == 200
        assert data['team']['name'] == 'PPP'

        # Change to h4x0r5, then back
        for name in ('h4x0r5', 'PPP'):
            team_req(client.patch, 1, name, key, 204)

        # Delete team
        data, status = api_req(client.delete, '/api/user/team', key)
        assert status == 204

        # Can't delete again
        data, status = api_req(client.delete, '/api/user/team', key)
        assert status == 403
        assert data['message'] == 'You must be part of a team.'

        # Create a new one
        team_req(client.post, None, 'PPP', key, 409, 'That team name is taken.')
        team_req(client.post, None, 'Hash Slinging Hackers', key, 201)

        # Team data
        data, status = api_req(client.get, '/api/teams/1')
        assert status == 200
        assert data == {
            'id': 1,
            'name': 'PPP',
            'points': 0,
            'flags': {},
        }

        # Can't rename to another team
        for name in ('PPP', 'Ppp'):
            team_req(client.patch, 2, name, key, 409, 'That team name is taken.')

        # Name changes, check that it changed
        # Note: h4x0r5 should NOT 409
        for name in ('Hash Slinging Hackers', 'h4x0r5',
                     'hash slinGING hackers', 'Hash Slinging Hackers'):
            team_req(client.patch, 2, name, key, 204)
            data, status = api_req(client.get, '/api/user', key)
            assert status == 200
            assert data['team']['name'] == name

        # Team perms
        team_req(client.patch, 1, 'PPP', key, 403,
                 'You are not a member of this team.')

        # Leaderboard
        data, status = api_req(client.get, '/api/teams/')
        assert status == 200
        assert data == {
            'teams': [
                {'id': 1, 'name': 'PPP', 'points': 0},
                {'id': 2, 'name': 'Hash Slinging Hackers', 'points': 0},
            ],
        }
