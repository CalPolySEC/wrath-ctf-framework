"""Core application logic."""
from base64 import urlsafe_b64encode
from bcrypt import gensalt, hashpw
from datetime import datetime
from flask import current_app
from werkzeug.security import safe_str_cmp
from ._compat import want_bytes
from .ext import db
from .models import Team, User, Challenge, Resource, Solve
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
    # This is pure mystical alchemy
    q = (db.session.query(Team, db.func.ifnull(db.func.sum(Challenge.points),
                                               0).label('points'))
         .filter(Team.hide_rank == 0)
         .outerjoin(Solve).outerjoin(Challenge).group_by(Team.id)
         .order_by(db.desc('points'), db.func.min(Solve.earned_on), Team.id))
    return q.all()


def get_team(id):
    return Team.query.get(id)


def get_team_by_name(name):
    return Team.query.filter(Team.name == name).first()


def get_name():
    return current_app.config['CTF']['name']


def check_prereqs(team, challenge):
    if challenge.prerequisites is None:
        return True
    else:
        return challenge.prerequisites <= team.challenges


def get_challenges(team):
    all_challs = Challenge.query.order_by(Challenge.points).all()
    return list(filter(lambda c: check_prereqs(team, c), all_challs))


def get_challenge(team, id):
    chal = Challenge.query.get(id)
    if chal is None or not check_prereqs(team, chal):
        return None
    else:
        return chal


def get_resource(team, category, name):
    resource = Resource.query.filter(Resource.name == name).\
               join(Challenge).\
               filter(Challenge.category == category).first()
    if resource is None or not check_prereqs(team, resource.challenge):
        return None
    else:
        return resource


def hash_fleg(fleg):
    return hashlib.sha256(want_bytes(fleg)).hexdigest()


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


def update_team(team, name=None, hide_rank=None):
    if name is None and hide_rank is None:
        # Nothing to do
        return

    if name is not None:
        if Team.query.filter((db.func.lower(Team.name) == name.lower()) &
                             (Team.id != team.id)).count():
            raise CtfException('That team name is taken.')
        team.name = name

    if hide_rank is not None:
        team.hide_rank = hide_rank

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

    fleg_hash = hash_fleg(fleg)
    solved = Challenge.query.filter_by(fleg_hash=fleg_hash).first()

    if solved is None:
        raise CtfException('Nope.')  # fleg incorrect
    elif solved in team.challenges:
        raise CtfException('You\'ve already entered that flag.')

    team.challenges.add(solved)
    db.session.add(team)
    db.session.commit()

    return solved
