# JSON Bourne API
from flask import Blueprint, request, g, abort, Response, jsonify, make_response
from functools import wraps
from . import ctf
from ._compat import text_type


bp = Blueprint('api', __name__)


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(404)
def handle_error(exc):
    return make_response(jsonify({'message': exc.description}), exc.code)


def json_value(key, desired_type=None):
    data = request.get_json()
    try:
        value = data[key]
    except (KeyError, TypeError):
        abort(400)
    if desired_type and not isinstance(value, desired_type):
        abort(400)
    return value


def require_auth(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        token = request.headers.get('X-Session-Key', '')
        g.team = ctf.team_for_token(token)
        if not g.team:
            abort(403, 'A valid X-Session-Key header is required.')
        return fn(*args, **kwargs)
    return inner


@bp.route('/teams/', methods=['POST'])
def create_team():
    name = json_value('team', text_type)
    team = ctf.create_team(name)
    if team is None:
        abort(400, 'That team name is taken.')
    return jsonify({
        'id': team.id,
        'name': team.name,
        'password': team.password,
    })


@bp.route('/sessions/', methods=['POST'])
def login():
    team = json_value('team', text_type)
    password = json_value('password', text_type)
    team = ctf.login_team(team, password)
    if not team:
        abort(403, 'Incorrect team name or password.')
    key = ctf.create_session_key(team.id)
    return jsonify({'key': key})


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
@require_auth
def submit_flag():
    fleg = json_value('flag', text_type)
    db_fleg, err_msg = ctf.add_flag(fleg, g.team)
    if db_fleg is None:
        abort(400, err_msg)
    return jsonify({'points_earned': db_fleg.level.points})
