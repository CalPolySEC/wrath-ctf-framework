# -*- coding: utf-8 -*-
from ctf import create_app
import fakeredis
import json
import pytest
import os


@pytest.fixture
def app():
    os.environ["CTF_CONFIG"] = "tests/test_config.json"
    app = create_app()
    app.redis = fakeredis.FakeRedis()
    app.secret_key = 'my secret key'
    app.debug = True
    return app


def api_req(fn, url, token=None, data=None, desired_status=None, err_msg=None):
    """Make an API request. If given, assert status code and error message."""
    kwargs = {'headers': {}}
    if token:
        kwargs['headers']['X-Session-Key'] = token
    if data is not None:
        kwargs['headers']['Content-Type'] = 'application/json'
        kwargs['data'] = json.dumps(data)

    rv = fn(url, **kwargs)

    if desired_status is not None:
        assert rv.status_code == desired_status

    if rv.data:
        try:
            result = json.loads(rv.data.decode('utf-8'))
        except ValueError:
            result = rv.data.decode('utf-8')
    else:
        result = None

    if err_msg is not None:
        assert result['message'] == err_msg

    return result


def auth(client, username='test'):
    data = api_req(client.post, '/api/users/', None, {
        'username': username,
        'password': 'test',
    }, 201)
    return data['key']


def test_user_auth(app):
    with app.test_client() as client:
        def create_user(username, password, status, message=None):
            return api_req(client.post, '/api/users/', None, {
                'username': username,
                'password': password,
            }, status, message)

        def login(username, password, status, message=None):
            return api_req(client.post, '/api/sessions/', None, {
                'username': username,
                'password': password,
            }, status, message)

        # Input checking
        api_req(client.post, '/api/users/', None, {}, 400,
                'Missing JSON value \'username\'.')
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
        for k in (None, '', 'bad.sig', 'fake.TPRM-X0i3azi4DyIqjQy_8jTbHo',
                  key[:-1]):
            msg = 'A valid X-Session-Key header is required.'
            api_req(client.get, '/api/user', k, None, 403, msg)

        api_req(client.get, '/api/user', key, 200)


def test_teams(app):
    with app.test_client() as client:
        key = auth(client)

        # Check that user team is null
        assert api_req(client.get, '/api/user', key, 200)['team'] is None

        # Create a team
        data = api_req(client.post, '/api/teams/', key, {'name': 'PPP'}, 201)
        assert data['id'] == 1
        for name in ('PPP', 'abc'):
            api_req(client.post, '/api/teams/', key, {'name': name}, 409,
                    'You are already a member of a team.')

        # Get user team
        data = api_req(client.get, '/api/user', key, 200)
        assert data['team']['name'] == 'PPP'

        # Get team directly
        assert api_req(client.get, '/api/team', key, 200)['name'] == 'PPP'

        # Change to h4x0r5, then back
        for name in ('h4x0r5', 'PPP'):
            api_req(client.patch, '/api/team', key, {'name': name}, 204)

        # Delete team
        api_req(client.delete, '/api/team', key, None, 204)

        # Can't delete again
        api_req(client.delete, '/api/team', key, None, 403,
                'You must be part of a team.')

        # Create a new one
        api_req(client.post, '/api/teams/', key, {'name': 'PPP'}, 409,
                'That team name is taken.')
        api_req(client.post, '/api/teams/', key,
                {'name': 'Hash Slinging Hackers'}, 201)

        # Team data
        assert api_req(client.get, '/api/teams/1', key, 200) == {
            'id': 1,
            'name': 'PPP',
            'points': 0,
        }

        # Can't rename to another team
        for name in ('PPP', 'Ppp'):
            api_req(client.patch, '/api/team', key, {'name': name}, 409,
                    'That team name is taken.')

        # Name changes, check that it changed
        # Note: h4x0r5 should NOT 409
        for name in ('Hash Slinging Hackers', 'h4x0r5', u'😊',
                     'hash slinGING hackers', 'Hash Slinging Hackers'):
            api_req(client.patch, '/api/team', key, {'name': name}, 204)
            data = api_req(client.get, '/api/user', key, None, 200)
            assert data['team']['name'] == name

        # Leaderboard
        assert api_req(client.get, '/api/teams/') == {
            'teams': [
                {'id': 1, 'name': 'PPP', 'points': 0},
                {'id': 2, 'name': 'Hash Slinging Hackers', 'points': 0},
            ],
        }


def test_invites(app):
    with app.test_client() as client:
        def invite_user(key, username, status, message=None):
            return api_req(client.post, '/api/team/members', key,
                           {'username': username}, status, message)

        def set_team(key, team, status, message=None):
            return api_req(client.patch, '/api/user', key, {'team': team},
                           status, message)

        key1 = auth(client, 'user1')
        key2 = auth(client, 'user😊')

        # Create a team
        post = {'name': 'PPP'}
        assert api_req(client.post, '/api/teams/', key1, post, 201)['id'] == 1

        # Permissions
        no_team_msg = 'You must be part of a team.'
        for username in ('user1', 'user😊', 'fakeuser'):
            invite_user(key2, username, 403, no_team_msg)

        invite_user(key1, 'abc', 400, 'There is no user with that name.')
        invite_user(key1, 'user1', 400,
                    'That user is already a member of this team.')

        # Bad type
        api_req(client.patch, '/api/user', key1, {'team': 'PPP'}, 400,
                'Expected \'team\' to be type int.')

        # Bad accepts
        set_team(key1, 1, 400, 'You have not been invited to this team.')
        set_team(key2, 1, 400, 'You have not been invited to this team.')
        set_team(key1, 1337, 400, 'You have not been invited to this team.')
        set_team(key2, 1337, 400, 'You have not been invited to this team.')

        # Valid invite
        invite_user(key1, 'user😊', 204)
        invite_user(key1, 'user😊', 400, 'That user has already been invited.')

        assert api_req(client.get, '/api/teams/invited/', key2, 200) == {
            'teams': [{
                'id': 1,
                'name': 'PPP',
            }],
        }

        set_team(key2, 1, 204)

        assert api_req(client.get, '/api/teams/invited/', key2, 200) == {
            'teams': [],
        }

        assert api_req(client.get, '/api/user', key2, 200)['team']['id'] == 1
