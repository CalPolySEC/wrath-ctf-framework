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
        abort(400)
    if desired_type and not isinstance(value, desired_type):
        abort(400)
    return value


def require_auth(view):
    @wraps(view)
    def inner(*args, **kwargs):
        token = request.headers.get('X-Session-Key', '')
        g.user = ctf.user_for_token(token)
        if not g.user:
            abort(403, 'A valid X-Session-Key header is required.')
        return view(*args, **kwargs)
    return inner


def require_team(view):
    @wraps(view)
    @require_auth
    def inner(*args, **kwargs):
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
    user = ctf.login(username, password)
    if not user:
        abort(403, 'Incorrect team name or password.')
    key = ctf.create_session_key(user.id)
    return jsonify({'key': key})


@bp.route('/users/me')
@require_auth
def me():
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
@require_auth
def create_team():
    name = json_value('name', text_type)
    try:
        team = ctf.create_team(g.user, name)
    except CtfException as exc:
        abort(400, exc.message)
    return jsonify({
        'id': team.id,
        'name': team.name,
    }), 201


@bp.route('/invites/')
@require_auth
def get_invites():
    return jsonify({
        'teams': [
            {
                'id': team.id,
                'name': team.name,
            } for team in g.user.invites
        ]
    })


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
@require_auth
def join_team():
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
