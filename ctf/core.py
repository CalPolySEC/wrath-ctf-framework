"""Core application logic."""
from base64 import urlsafe_b64encode
from bcrypt import gensalt, hashpw
from datetime import datetime
from flask import current_app
from werkzeug.security import safe_str_cmp
from ._compat import want_bytes
from .ext import db
from .models import Team, User, Fleg
import hashlib
import os


class CtfException(Exception):

    def __init__(self, message):
        self.message = message


def ensure_active():
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    now = datetime.utcnow()
    start = datetime.strptime(current_app.config['CTF']['start_time'], fmt)
    end = datetime.strptime(current_app.config['CTF']['end_time'], fmt)
    if now < start:
        raise CtfException('The competition has not started yet. Calm down.')
    elif now > end:
        raise CtfException('The competition has ended!')


def get_teams():
    # TODO: Team.points ought to be a SQL sum instead of denormalized
    return Team.query.order_by(Team.points.desc(), Team.last_fleg).all()


def get_team(id):
    return Team.query.get(id)


def create_session_key(user):
    token = urlsafe_b64encode(os.urandom(24)).decode('ascii')
    current_app.redis.set(u'api-token.%s' % token, user.id)
    return token


def user_for_token(token):
    user_id = current_app.redis.get('api-token.%s' % token)
    if not user_id:
        return None
    return User.query.filter_by(id=int(user_id)).first()


def create_user(username, password):
    if User.query.filter(db.func.lower(User.name) == username.lower()).count():
        raise CtfException('That username is taken.')
    pw_hash = hashpw(want_bytes(password), gensalt())
    user = User(name=username, password=pw_hash)
    db.session.add(user)
    db.session.commit()
    return user


def login(username, password):
    dummy_salt = gensalt()
    user = User.query.filter(db.func.lower(User.name) == username.lower()) \
        .first()
    if user:
        correct = want_bytes(user.password)
        pw_hash = hashpw(want_bytes(password), correct)
        if safe_str_cmp(pw_hash, correct):
            return user
    else:
        # Defeat username discovery
        hashpw(want_bytes(password), dummy_salt)
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


def rename_team(team, name):
    if Team.query.filter((db.func.lower(Team.name) == name.lower()) &
                         (Team.id != team.id)).count():
        raise CtfException('That team name is taken.')
    team.name = name
    db.session.add(team)
    db.session.commit()


def create_invite(team, username):
    user = User.query.filter(db.func.lower(User.name) == username.lower()) \
                .first()
    if not user:
        raise CtfException('There is no user with that name.')
    elif user.team == team:
        raise CtfException('That user is already a member of this team.')
    elif user in team.invited:
        raise CtfException('That user has already been invited.')
    team.invited.append(user)
    db.session.add(team)
    db.session.commit()


def join_team(team_id, user):
    team = Team.query.get(team_id)
    if not team or team not in user.invites:
        raise CtfException('You have not been invited to this team.')
    user.team = team
    user.invites.remove(team)
    db.session.add(user)
    db.session.commit()


def leave_team(user):
    user.team = None
    db.session.add(user)
    db.session.commit()


def add_fleg(fleg, team):
    ensure_active()

    fleg_hash = hashlib.sha256(want_bytes(fleg)).hexdigest()
    db_fleg = Fleg.query.filter_by(hash=fleg_hash).first()

    if db_fleg is None:
        raise CtfException('Nope.')  # fleg incorrect
    elif db_fleg.level in team.levels:
        raise CtfException('You\'ve already entered that flag.')

    team.levels.append(db_fleg.level)
    team.points += db_fleg.level.points
    team.last_fleg = db.func.now()
    db.session.add(team)
    db.session.commit()

    return db_fleg
