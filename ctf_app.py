from datetime import datetime
from flask import Flask, request, session, redirect, render_template, url_for,\
                  flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from getwords import getwords
from hashlib import sha256
from random import choice
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, Forbidden, NotFound, InternalServerError
import os
import string


app = Flask(__name__, static_url_path=os.environ.get('STATIC_PREFIX', '/static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'not secure brah')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


association_table = db.Table('team_flags', db.Model.metadata,
    db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
    db.Column('flag_id', db.Integer, db.ForeignKey('flag.id'))
)


class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64))
    points = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    level = db.Column(db.Integer)
    teams = db.relationship('Team', secondary=association_table)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(20))
    levels = db.relationship('Flag', backref='category')


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    points = db.Column(db.Integer, default=0)
    flags = db.relationship('Flag', secondary=association_table)
    last_flag = db.Column(db.DateTime, server_default=db.func.now())


def random_string(size):
    letters = string.ascii_letters + string.digits
    return ''.join(choice(letters) for n in range(size))


@app.before_request
def create_csrf():
    if 'csrf_token' not in session:
        session['csrf_token'] = random_string(32)


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def handle_error(exc):
    if not isinstance(exc, HTTPException):
        exc = InternalServerError()
    return render_template('error.html', error=exc), exc.code


def require_auth(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if 'team' not in session:
            flash('You must be logged in to a team to do that.', 'danger')
            return redirect(url_for('login_page'), code=303)
        return fn(*args, **kwargs)
    return inner


@app.route('/')
def home_page():
    teams = Team.query.order_by(Team.points.desc(), Team.last_flag).all()
    return render_template('home.html', teams=teams)


@app.route('/login/')
def login_page():
    return render_template('login.html')


@app.route('/about/')
def about_page():
    return render_template('about.html')


@app.route('/contact/')
def contact_page():
    return render_template('contact.html')


@app.route('/submit/')
@require_auth
def flag_page():
    return render_template('submit.html')


@app.route('/teams/<int:id>/')
def team_page(id):
    team = Team.query.filter_by(id=id).first()
    if team is None:
        raise NotFound()
    cat_query = Category.query.order_by(Category.order.asc())
    categories = [(cat.name, cat.levels) for cat in cat_query]
    return render_template('team.html', team=team, categories=categories)


@app.route('/teams', methods=['POST'])
def new_team():
    """Create a new team, with a generated password."""
    name = request.form.get('name', '')
    if not name:
        flash('You must supply a team name.', 'danger')
        return redirect(url_for('login_page'), code=303)
    if Team.query.filter(func.lower(Team.name) == name.lower()).count() > 0:
        flash('That team name is taken.', 'danger')
        return redirect(url_for('login_page'), code=303)

    password = getwords()
    team = Team(name=name, password=password)
    db.session.add(team)
    db.session.commit()
    session['team'] = team.id
    flash('Team successfully created.', 'success')
    return redirect(url_for('team_page', id=team.id), code=303)


@app.route('/auth_team', methods=['POST'])
def auth_team():
    name = request.form.get('name', '')
    password = request.form.get('password', '')
    team = Team.query.filter(func.lower(Team.name) == name.lower()).first()

    if team is None:
        flash('No team exists with that name.', 'danger')
        return redirect(url_for('login_page'), code=303)
    if password != team.password:
        flash('Incorrect team password.', 'danger')
        return redirect(url_for('login_page'), code=303)

    session['team'] = team.id
    return redirect(url_for('team_page', id=team.id), code=303)


@app.route('/logout')
@require_auth
def logout():
    """Remove the team, and cycle the token."""
    if request.args.get('token') != session['csrf_token']:
        raise Forbidden()
    del session['team']
    del session['csrf_token']
    return redirect(url_for('home_page'), code=303)


@app.route('/flags', methods=['POST'])
@require_auth
def submit_flag():
    flag = request.form.get('flag', '')
    flag_hash = sha256(flag.encode('utf-8')).hexdigest()
    db_flag = Flag.query.filter_by(hash=flag_hash).first()
    team = Team.query.filter_by(id=session['team']).first()

    if db_flag is None:
        flash('Sorry, the flag you entered is not correct.', 'danger')
    elif db_flag in team.flags:
        flash('You\'ve already entered that flag.', 'warning')
    elif db.session.query(Flag).filter(Flag.category == db_flag.category) \
            .filter(Flag.level < db_flag.level) \
            .filter(~Flag.teams.any(id=team.id)).count() > 0:
        flash('You must complete all previous challenges first!', 'danger')
    else:
        team.flags.append(db_flag)
        team.points += db_flag.points
        team.last_flag = datetime.now()
        db.session.add(team)
        db.session.commit()
        flash('Correct! You have earned {0} points for your team.'
              .format(db_flag.points), 'success')

    return redirect(url_for('flag_page'), code=303)


if __name__ == '__main__':
    app.run(debug=True)
