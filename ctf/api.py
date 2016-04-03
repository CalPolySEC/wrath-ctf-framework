# JSON Bourne API
from flask import Blueprint, request, g, abort, Response, jsonify, make_response
from functools import wraps
from . import ctf
from ._compat import text_type
from .ctf import CtfException


bp = Blueprint('api', __name__)


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(404)
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
    token = request.headers.get('X-Session-Key', '')
    g.user = ctf.user_for_token(token)
    if not g.user:
        abort(403, 'A valid X-Session-Key header is required.')


def require_team(view):
    @wraps(view)
    def inner(*args, **kwargs):
        ensure_auth()
        g.team = g.user.team
        if g.team is None:
            abort(403, 'You must be part of a team.')
        return view(*args, **kwargs)
    return inner


@bp.route('/users/', methods=['POST'])
def create_user():
    username = json_value('username', text_type)
    password = json_value('password', text_type)
    try:
        user = ctf.create_user(username, password)
    except CtfException as exc:
        abort(400, exc.message)
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


@bp.route('/users/me')
def me():
    ensure_auth()
    user_obj = {
        'id': g.user.id,
        'username': g.user.name,
        'team': None,
    }
    if g.user.team is not None:
        user_obj['team'] = {
            'id': g.user.team.id,
            'name': g.user.team.name,
        }
    return jsonify(user_obj)


@bp.route('/teams/', methods=['POST'])
def create_team():
    ensure_auth()
    name = json_value('name', text_type)
    try:
        team = ctf.create_team(g.user, name)
    except CtfException as exc:
        abort(400, exc.message)
    return jsonify({
        'id': team.id,
        'name': team.name,
    }), 201


@bp.route('/invites/', methods=['POST'])
@require_team
def create_invite():
    user = json_value('user', text_type)
    try:
        ctf.create_invite(g.team, user)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/users/me/team', methods=['PUT'])
def join_team():
    ensure_auth()
    team_id = json_value('team', int)
    try:
        ctf.join_team(team_id, g.user)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/users/me/team', methods=['DELETE'])
@require_team
def leave_team():
    ctf.leave_team(g.user, g.team)
    return Response(status=204)


@bp.route('/teams/')
def leaderboard():
    if request.args.get('invited', 'false') != 'false':
        ensure_auth()
        teams = g.user.invites
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


@bp.route('/flags/', methods=['POST'])
@require_team
def submit_flag():
    fleg = json_value('flag', text_type)
    try:
        db_fleg = ctf.add_flag(fleg, g.team)
    except CtfException as exc:
        abort(400, exc.message)
    return jsonify({'points_earned': db_fleg.level.points}), 201
