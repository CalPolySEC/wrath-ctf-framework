"""Core application logic."""
from base64 import urlsafe_b64encode
from bcrypt import gensalt, hashpw
from datetime import datetime
from flask import current_app
from itsdangerous import Signer, BadSignature, want_bytes
from werkzeug.security import safe_str_cmp
from .models import db, Team, User, Flag, Level, Category
import hashlib
import os


class CtfException(Exception):

    def __init__(self, message):
        self.message = message


def has_ended():
    end = current_app.config['END_TIME_UTC']
    if end is None:
        return False
    return datetime.utcnow() > datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%fZ')


def get_teams():
    return Team.query.order_by(Team.points.desc(), Team.last_flag).all()


def get_team(id):
    return Team.query.filter_by(id=id).first()


def get_categories():
    cat_query = Category.query.order_by(Category.order.asc())
    return [(cat.name, cat.levels) for cat in cat_query]


def get_signer(app):
    return Signer(app.secret_key, salt='wrath-ctf')


def create_session_key(user_id):
    token = urlsafe_b64encode(os.urandom(24))
    current_app.redis.set(b'api-token.%s' % token, user_id)
    signer = get_signer(current_app)
    return signer.sign(token).decode('ascii')


def user_for_token(session_key):
    signer = get_signer(current_app)
    try:
        token = signer.unsign(session_key)
    except BadSignature:
        return None
    user_id = current_app.redis.get(b'api-token.%s' % token)
    if not user_id:
        return None
    return User.query.filter_by(id=int(user_id)).first()


def create_user(username, password):
    if not username or not password:
        raise CtfException('You must supply a username and password.')
    if User.query.filter(db.func.lower(User.name) == username.lower()).count():
        raise CtfException('That username is taken.')
    pw_hash = hashpw(password.encode('utf-8'), gensalt())
    user = User(name=username, password=pw_hash)
    db.session.add(user)
    db.session.commit()
    return user


def login(username, password):
    user = User.query.filter(db.func.lower(User.name) == username.lower()).first()
    if user:
        pw_hash = hashpw(password.encode('utf-8'), user.password)
        if safe_str_cmp(pw_hash, user.password):
            return user
    else:
        # Break timing attacks
        hashpw(password.encode('utf-8'), gensalt())
    raise CtfException('Incorrect username or password.')


def create_team(user, name):
    if user.team:
        raise CtfException('You are already a member of a team.')
    elif Team.query.filter(db.func.lower(Team.name) == name.lower()).count():
        raise CtfException('That team name is taken.')
    team = Team(name=name)
    user.team = team
    db.session.add(team)
    db.session.commit()
    return team


def create_invite(team, username):
    user = User.query.filter(db.func.lower(User.name) == username.lower()).first()
    if not user:
        raise CtfException('There is no user with that name.')
    elif user in team.invited:
        raise CtfException('That user has already been invited.')
    team.invited.append(user)
    db.session.add(team)
    db.session.commit()


def join_team(team_id, user):
    team = Team.query.filter_by(id=team_id).first()
    if not team or team not in user.invites:
        raise CtfException('You have not been invited to this team.')
    user.team = team
    db.session.add(user)
    db.session.commit()


def leave_team(user, team):
    if user.team != team:
        raise CtfException('The user is not a member of this team.')
    user.team = None
    db.session.add(user)
    db.session.commit()


def add_flag(fleg, team):
    if has_ended():
        raise CtfException('The competition has ended, sorry.')

    fleg_hash = hashlib.sha256(fleg.encode('utf-8')).hexdigest()
    db_fleg = Flag.query.filter_by(hash=fleg_hash).first()

    if db_fleg is None:
        raise CtfException('Sorry, the flag you entered is not correct.')
    elif db_fleg.level in team.levels:
        raise CtfException('You\'ve already entered that flag.')

    team.levels.append(db_fleg.level)
    team.points += db_fleg.level.points
    team.last_flag = db.func.now()
    db.session.add(team)
    db.session.commit()

    return db_fleg
