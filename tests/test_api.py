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


def auth(client, username='test'):
    data, status = api_req(client.post, '/api/users/', None, {
        'username': username,
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

        create_user(1, '', 400, 'Expected \'username\' to be type string.')

        # User creation
        create_user('', '', 400, 'You must supply a username and password.')

        data = create_user('test', 'test😊', 201)
        assert 'key' in data

        create_user('test', 'badpw', 409, 'That username is taken.')

        # Login
        login('abc', 'badpw', 403, 'Incorrect username or password.')
        login('test', 'badpw', 403, 'Incorrect username or password.')
        login('test', 'test', 403, 'Incorrect username or password.')

        data = login('test', 'test😊', 201)
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


def test_invites(app):
    with app.test_client() as client:
        def invite_user(key, team, username, status, message=None):
            data, code = api_req(client.post, '/api/teams/%d/members' % team,
                                   key, {'username': username})
            assert code == status
            if message:
                assert data['message'] == message
            return data

        def set_team(key, team, status, message=None):
            data, code = api_req(client.patch, '/api/user/team', key,
                                 {'team': team})
            assert code == status
            if message:
                assert data['message'] == message
            return data

        key1 = auth(client, 'user1')
        key2 = auth(client, 'user2')

        # Create a team
        data, status = api_req(client.post, '/api/teams/', key1, {
            'name': 'PPP',
        })
        assert status == 201
        assert data['id'] == 1

        # Permissions
        invite_user(key2, 1, 'user1', 403,
                    'You are not a member of this team.')
        invite_user(key2, 1, 'user2', 403,
                    'You are not a member of this team.')
        invite_user(key1, 1337, 'user2', 403,
                    'You are not a member of this team.')
        invite_user(key2, 1337, 'user2', 403,
                    'You are not a member of this team.')
        invite_user(key1, 1, 'abc', 400, 'There is no user with that name.')
        invite_user(key1, 1, 'user1', 400,
                    'That user is already a member of this team.')

        # Bad type
        data, status = api_req(client.patch, '/api/user/team', key1,
                               {'team': 'PPP'})
        assert status == 400
        assert data['message'] == 'Expected \'team\' to be type int.'

        # Bad accepts
        set_team(key1, 1, 400, 'You have not been invited to this team.')
        set_team(key2, 1, 400, 'You have not been invited to this team.')
        set_team(key1, 1337, 400, 'You have not been invited to this team.')
        set_team(key2, 1337, 400, 'You have not been invited to this team.')

        # Valid invite
        invite_user(key1, 1, 'user2', 204)
        invite_user(key1, 1, 'user2', 400,
                    'That user has already been invited.')
        set_team(key2, 1, 204)

        data, status = api_req(client.get, '/api/teams/invited/', key2)
        assert status == 200
        assert data == {'teams': [{
            'id': 1,
            'name': 'PPP',
        }]}

        data, status = api_req(client.get, '/api/user', key2)
        assert status == 200
        assert data['team']['id'] == 1
