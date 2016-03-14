from datetime import datetime
from flask import current_app
from .getwords import getwords
from .models import db, Team, Flag, Level, Category
import hashlib


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


def login_team(username, password):
    team = Team.query.filter(db.func.lower(Team.name) == name.lower()).first()
    if team is None or not safe_str_cmp(password, team.password):
        return None
    return team


def create_team(name):
    if Team.query.filter(db.func.lower(Team.name) == name.lower()).count():
        return None
    team = Team(name=name, password=getwords())
    db.session.add(team)
    db.session.commit()
    return team


def add_flag(fleg, team_id):
    if has_ended():
        return None, 'The competition has ended, sorry.'

    fleg_hash = hashlib.sha256(fleg.encode('utf-8')).hexdigest()
    db_fleg = Flag.query.filter_by(hash=fleg_hash).first()
    team = get_team(team_id)

    if db_fleg is None:
        return None, 'Sorry, the flag you entered is not correct.'
    elif db_fleg.level in team.levels:
        return None, 'You\'ve already entered that flag.'

    team.levels.append(db_fleg.level)
    team.points += db_fleg.level.points
    team.last_flag = func.now()
    db.session.add(team)
    db.session.commit()

    return db_fleg
