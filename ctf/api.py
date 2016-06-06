"""JSON Bourne API"""
from flask import Blueprint, request, current_app, abort, Response, jsonify
from itsdangerous import Signer, BadSignature, want_bytes
from werkzeug import exceptions
from . import core, ext
from ._compat import text_type
from .core import CtfException


bp = Blueprint('api', __name__)
ext.csrf.exempt(bp)


def handle_error(exc):
    return jsonify({'message': exc.description}), exc.code


for code in exceptions.default_exceptions.keys():
    if code != 500:
        bp.errorhandler(code)(handle_error)


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
        abort(400, 'Expected \'{0}\' to be type {1}.'.format(key, type_name))
    return value


def get_signer():
    return Signer(current_app.secret_key, salt='wrath-ctf')


def ensure_user():
    header_name = 'X-Session-Key'
    err_msg = 'A valid {0} header is required.'.format(header_name)
    key = request.headers.get(header_name, '')
    try:
        signer = get_signer()
        token = signer.unsign(key).decode('utf-8')
    except (BadSignature, ValueError):
        abort(403, err_msg)
    user = core.user_for_token(token)
    if user is None:
        abort(403, err_msg)
    return user


def ensure_team(user=None):
    """Return the team for the current user, or 403 if there is none.

    user is optional. If omitted, it will be determined from ensure_user(). Be
    careful when you supply this parameter, make sure it came from a call to
    ensure_user().
    """
    if user is None:
        user = ensure_user()
    team = core.team_for_user(user)
    if team is None:
        abort(403, 'You must be part of a team.')
    return user.team


def create_signed_key(user):
    """Generate a valid auth token for the user, and sign it."""
    key = core.create_session_key(user)
    signer = get_signer()
    return signer.sign(want_bytes(key)).decode('ascii')


@bp.route('/users/', methods=['POST'])
def create_user():
    username = json_value('username', text_type)
    password = json_value('password', text_type)
    if not username or not password:
        abort(400, 'You must supply a username and password.')
    try:
        user = core.create_user(username, password)
    except CtfException as exc:
        abort(409, exc.message)
    key = create_signed_key(user)
    return jsonify({'key': key}), 201


@bp.route('/sessions/', methods=['POST'])
def login():
    username = json_value('username', text_type)
    password = json_value('password', text_type)
    try:
        user = core.login(username, password)
    except CtfException as exc:
        abort(403, exc.message)
    key = create_signed_key(user)
    return jsonify({'key': key}), 201


@bp.route('/user')
def me():
    user = ensure_user()
    user_obj = {
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
    user = ensure_user()
    name = json_value('name', text_type)
    try:
        team = core.create_team(user, name)
    except CtfException as exc:
        abort(409, exc.message)
    return jsonify({
        'id': team.id,
        'name': team.name,
    }), 201


@bp.route('/teams/invited/')
def invited_teams():
    user = ensure_user()
    teams = user.invites
    return jsonify({
        'teams': [{
            'id': team.id,
            'name': team.name,
        } for team in teams],
    })


@bp.route('/user', methods=['PATCH'])
def join_team():
    user = ensure_user()
    team_id = json_value('team', int)
    try:
        core.join_team(team_id, user)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/team', methods=['DELETE'])
def leave_team():
    user = ensure_user()
    ensure_team(user=user)
    core.leave_team(user)
    return Response(status=204)


@bp.route('/teams/')
def leaderboard():
    teams = core.get_teams()
    return jsonify({
        'teams': [{
            'id': team.id,
            'name': team.name,
            'points': team.points,
        } for team in teams],
    })


@bp.route('/teams/<int:id>')
def get_team(id):
    team = core.get_team(id)
    return jsonify({
        'id': team.id,
        'name': team.name,
        'points': team.points,
    })


@bp.route('/team')
def my_team():
    team = ensure_team()
    return get_team(team.id)


@bp.route('/team', methods=['PATCH'])
def rename_team():
    team = ensure_team()
    name = json_value('name', text_type)
    try:
        team = core.rename_team(team, name)
    except CtfException as exc:
        abort(409, exc.message)
    return Response(status=204)


@bp.route('/team/members', methods=['POST'])
def invite_user():
    team = ensure_team()
    user = json_value('username', text_type)
    try:
        core.create_invite(team, user)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/flags/', methods=['POST'])
def submit_fleg():
    team = ensure_team()
    fleg = json_value('flag', text_type)
    try:
        db_fleg = core.add_fleg(fleg, team)
    except CtfException as exc:
        abort(400, exc.message)
    return jsonify({'points_earned': db_fleg.level.points}), 201
