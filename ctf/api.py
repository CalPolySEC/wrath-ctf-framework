# JSON Bourne API
from flask import Blueprint, request, g, abort, Response, jsonify
from functools import wraps
from . import ctf
from ._compat import text_type
from .ctf import CtfException


bp = Blueprint('api', __name__)


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(404)
@bp.errorhandler(409)
def handle_error(exc):
    return jsonify({'message': exc.description}), exc.code


def json_value(key, desired_type=None):
    data = request.get_json()
    try:
        value = data[key]
    except (KeyError, TypeError):
        abort(400, 'Missing JSON value \'{0}\'.'.format(key))
    if desired_type and not isinstance(value, desired_type):
        if desired_type == text_type:
            type_name = 'string'
        else:
            type_name = desired_type.__name__
        abort(400, 'Expected {0} for \'{1}\'.'.format(type_name, key))
    return value


def ensure_auth():
    header_name = 'X-Session-Key'
    err_msg = 'A valid {0} header is required.'.format(header_name)
    token = request.headers.get(header_name)
    if token is None:
        abort(403, err_msg)
    user = ctf.user_for_token(token)
    if not user:
        abort(403, err_msg)
    return user


def ensure_team(user=None, id=None):
    """Return the team for the current user, or 403 if there is none.

    user is optional. If omitted, it will be determined from ensure_auth(). Be
    careful when you supply this parameter, make sure it came from a call to
    ensure_auth().

    id is optional, will 403 if the team does not match the given id.
    """
    if user is None:
        user = ensure_auth()
    team = ctf.team_for_user(user)
    if team is None:
        abort(403, 'You must be part of a team.')
    elif id and team.id != id:
        abort(403, 'You are not a member of this team.')
    return user.team


@bp.route('/users/', methods=['POST'])
def create_user():
    username = json_value('username', text_type)
    password = json_value('password', text_type)
    if not username or not password:
        abort(400, 'You must supply a username and password.')
    try:
        user = ctf.create_user(username, password)
    except CtfException as exc:
        abort(409, exc.message)
    key = ctf.create_session_key(user.id)
    return jsonify({'key': key}), 201


@bp.route('/sessions/', methods=['POST'])
def login():
    username = json_value('username', text_type)
    password = json_value('password', text_type)
    try:
        user = ctf.login(username, password)
    except CtfException as exc:
        abort(403, exc.message)
    key = ctf.create_session_key(user.id)
    return jsonify({'key': key}), 201


@bp.route('/user')
def me():
    user = ensure_auth()
    user_obj = {
        'id': user.id,
        'username': user.name,
        'team': None,
    }
    if user.team is not None:
        user_obj['team'] = {
            'id': user.team.id,
            'name': user.team.name,
        }
    return jsonify(user_obj)


@bp.route('/teams/', methods=['POST'])
def create_team():
    user = ensure_auth()
    name = json_value('name', text_type)
    try:
        team = ctf.create_team(user, name)
    except CtfException as exc:
        abort(409, exc.message)
    return jsonify({
        'id': team.id,
        'name': team.name,
    }), 201


@bp.route('/user/team', methods=['PATCH'])
def join_team():
    user = ensure_auth()
    team_id = json_value('team', int)
    try:
        ctf.join_team(team_id, user)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/user/team', methods=['DELETE'])
def leave_team():
    user = ensure_auth()
    ensure_team(user=user)
    ctf.leave_team(user)
    return Response(status=204)


@bp.route('/teams/')
def leaderboard():
    if request.args.get('invited', 'false') != 'false':
        user = ensure_auth()
        teams = user.invites
    else:
        teams = ctf.get_teams()
    return jsonify({
        'teams': [{
            'id': team.id,
            'name': team.name,
            'points': team.points,
        } for team in teams],
    })


@bp.route('/teams/<int:id>')
def teams(id):
    team = ctf.get_team(id)
    categories = ctf.get_categories()
    return jsonify({
        'team': {
            'id': team.id,
            'name': team.name,
            'points': team.points,
            'flags': {
                category:
                [level.level for level in levels if level in team.levels]
            for category, levels in categories},
        },
    })


@bp.route('/teams/<int:id>', methods=['PATCH'])
def rename_team(id):
    team = ensure_team(id=id)
    name = json_value('name', text_type)
    try:
        team = ctf.rename_team(team, name)
    except CtfException as exc:
        abort(409, exc.message)
    return Response(status=204)


@bp.route('/teams/<int:id>/members', methods=['POST'])
def invite_user(id):
    team = ensure_team(id=id)
    user = json_value('username', text_type)
    try:
        ctf.create_invite(g.team, user)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/flags/', methods=['POST'])
def submit_flag():
    team = ensure_team()
    fleg = json_value('flag', text_type)
    try:
        db_fleg = ctf.add_flag(fleg, team)
    except CtfException as exc:
        abort(400, exc.message)
    return jsonify({'points_earned': db_fleg.level.points}), 201
