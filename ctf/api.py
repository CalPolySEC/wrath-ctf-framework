"""JSON Bourne API"""
from flask import Blueprint, request, current_app, abort, Response, jsonify, \
    send_from_directory
from itsdangerous import Signer, BadSignature, want_bytes
from werkzeug import exceptions
from functools import wraps
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


def get_json_value(data, key, desired_type, optional):
    """Return data[key], with type checking."""
    try:
        value = data[key]
    except (KeyError, TypeError):
        if optional:
            return None
        abort(400, "Missing JSON value '{0}'.".format(key))

    if desired_type is not None and not isinstance(value, desired_type):
        if desired_type == text_type:
            type_name = 'string'
        else:
            type_name = desired_type.__name__
        abort(400, "Expected '{0}' to be type {1}.".format(key, type_name))

    return value


def param(key, desired_type=None, optional=False):
    """Return a decorator to parse a JSON request value."""
    def decorator(view_func):
        """The actual decorator"""
        @wraps(view_func)
        def inner(*args, **kwargs):
            data = request.get_json()  # May raise a 400
            kwargs[key] = get_json_value(data, key, desired_type, optional)
            return view_func(*args, **kwargs)
        return inner
    return decorator


def get_signer():
    return Signer(current_app.secret_key, salt='wrath-ctf')


def ensure_user(view_func):
    """Decorator that errors if the user is not logged in.

    This is analagous to frontend.ensure_user
    """
    @wraps(view_func)
    def inner(*args, **kwargs):
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
        return view_func(user, *args, **kwargs)
    return inner


def ensure_team(view_func):
    """Decorator that errors if the user is not part of a team.

    This is analagous to frontend.ensure_team
    """
    @wraps(view_func)
    @ensure_user
    def inner(user, *args, **kwargs):
        if user.team is None:
            abort(403, 'You must be part of a team.')
        return view_func(user.team, *args, **kwargs)
    return inner


def create_signed_key(user):
    """Generate a valid auth token for the user, and sign it."""
    key = core.create_session_key(user)
    signer = get_signer()
    return signer.sign(want_bytes(key)).decode('ascii')


@bp.route('/users/', methods=['POST'])
@param('username', text_type)
@param('password', text_type)
def create_user(username, password):
    if not username or not password:
        abort(400, 'You must supply a username and password.')
    try:
        user = core.create_user(username, password)
    except CtfException as exc:
        abort(409, exc.message)
    key = create_signed_key(user)
    return jsonify({'key': key}), 201


@bp.route('/sessions/', methods=['POST'])
@param('username', text_type)
@param('password', text_type)
def login(username, password):
    try:
        user = core.login(username, password)
    except CtfException as exc:
        abort(403, exc.message)
    key = create_signed_key(user)
    return jsonify({'key': key}), 201


@bp.route('/user')
@ensure_user
def me(user):
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
@ensure_user
@param('name', text_type)
def create_team(user, name):
    try:
        team = core.create_team(user, name)
    except CtfException as exc:
        abort(409, exc.message)
    return jsonify({
        'id': team.id,
        'name': team.name,
    }), 201


@bp.route('/teams/invited/')
@ensure_user
def invited_teams(user):
    teams = user.invites
    return jsonify({
        'teams': [{
            'id': team.id,
            'name': team.name,
        } for team in teams],
    })


@bp.route('/user', methods=['PATCH'])
@ensure_user
@param('team', int)
def join_team(user, team):
    try:
        core.join_team(team, user)
    except CtfException as exc:
        abort(403, exc.message)
    return Response(status=204)


@bp.route('/team', methods=['DELETE'])
@ensure_user
def leave_team(user):
    # Note: same logic as ensure_team
    if user.team is None:
        abort(403, 'You must be part of a team.')
    core.leave_team(user)
    return Response(status=204)


@bp.route('/teams/')
def leaderboard():
    teams = core.get_teams()
    return jsonify({
        'teams': [{
            'id': team.id,
            'name': team.name,
            'points': points,
        } for team, points in teams],
    })


@bp.route('/teams/<int:id>')
def get_team(id):
    team = core.get_team(id)
    if team is None:
        abort(404)
    return jsonify({
        'id': team.id,
        'name': team.name,
        'points': team.get_points(),
    })


@bp.route('/team')
@ensure_team
def my_team(team):
    return get_team(team.id)


@bp.route('/team', methods=['PATCH'])
@ensure_team
@param('name', text_type, optional=True)
@param('hide_rank', bool, optional=True)
def rename_team(team, name, hide_rank):
    try:
        core.update_team(team, name, hide_rank)
    except CtfException as exc:
        abort(409, exc.message)
    return Response(status=204)


@bp.route('/team/members', methods=['POST'])
@ensure_team
@param('username', text_type)
def invite_user(team, username):
    try:
        core.create_invite(team, username)
    except CtfException as exc:
        abort(400, exc.message)
    return Response(status=204)


@bp.route('/flags/', methods=['POST'])
@ensure_team
@param('flag', text_type)
def submit_fleg(team, flag):
    try:
        solved = core.add_fleg(flag, team)
    except CtfException as exc:
        abort(400, exc.message)
    return jsonify({'points_earned': solved.points}), 201


@bp.route('/challenges/')
@ensure_team
def view_challenges(team):
    chal_dicts = map(lambda c: c.chal_info(), core.get_challenges(team))
    return jsonify({"challenges": list(chal_dicts)})


@bp.route('/challenges/<int:id>/')
@ensure_team
def challenge_info(team, id):
    chal = core.get_challenge(team, id)
    ret = chal.chal_info()
    ret.update({"solved": chal in team.challenges})
    return jsonify(ret)


@bp.route('/file/<category>/<name>')
@ensure_team
def get_resource(team, category, name):
    resource = core.get_resource(team, category, name)
    if resource is None:
        abort(404)
    else:
        return send_from_directory(resource.path, resource.name)
