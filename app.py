from base64 import urlsafe_b64encode
from flask import Flask, request, session, redirect, render_template, url_for,\
                  flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from getwords import getwords
from hashlib import sha256
from sqlalchemy import func
from werkzeug.exceptions import HTTPException, BadRequest, NotFound, InternalServerError
from werkzeug.security import safe_str_cmp
import os
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


app = Flask(__name__, static_url_path=os.environ.get('STATIC_PREFIX', '/static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'not secure brah')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.before_first_request
def create_db():
    db.create_all()


association_table = db.Table('team_levels', db.Model.metadata,
    db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
    db.Column('level_id', db.Integer, db.ForeignKey('level.id'))
)


class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64))
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'))
    level = db.relationship("Level")


class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer)
    level = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    teams = db.relationship('Team', secondary=association_table)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(20))
    levels = db.relationship('Level', backref='category')


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    points = db.Column(db.Integer, default=0)
    levels = db.relationship('Level', secondary=association_table)
    last_flag = db.Column(db.DateTime, server_default=db.func.now())


def is_safe_url(url):
    """Determine whether a URL is safe for redirection."""
    u = urlparse(url)
    return u.scheme == '' and u.netloc == '' and u.path != request.path


CSRF_BYTES = 36
@app.before_request
def create_csrf():
    """Generate a cryptographically secure CSRF token for every session."""
    if 'csrf_token' not in session:
        token = urlsafe_b64encode(os.urandom(CSRF_BYTES)).decode('utf-8')
        session['csrf_token'] = token


def ensure_csrf(token):
    """Show 400 Bad Request for a missing/incorrect CSRF token."""
    if token != session.get('csrf_token'):
        flash('Missing or incorrect CSRF token.', 'danger')
        raise BadRequest()


@app.before_request
def check_csrf():
    """Enforce CSRF tokens on all POST requests.

    We're assuming that no requests use PUT or DELETE methods.
    """
    if request.method == 'POST':
        ensure_csrf(request.form.get('token'))


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
    """Redirect to the login page if the user is not authenticated."""
    @wraps(fn)
    def inner(*args, **kwargs):
        if 'team' not in session:
            flash('You must be logged in to a team to do that.', 'danger')
            return redirect(url_for('login_page', next=request.path), code=303)
        return fn(*args, **kwargs)
    return inner


@app.route('/')
def home_page():
    teams = Team.query.order_by(Team.points.desc(), Team.last_flag).all()
    return render_template('home.html', teams=teams)


@app.route('/login/')
def login_page():
    return render_template('login.html')


@app.route('/submit/')
@require_auth
def flag_page():
    return render_template('submit.html')


@app.route('/teams/<int:id>/')
def team_page(id):
    """Get the page for a specific team."""
    team = Team.query.filter_by(id=id).first_or_404()
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

    redirect_url = request.args.get('next')
    if not redirect_url or not is_safe_url(redirect_url):
        redirect_url = url_for('team_page', id=team.id)
    return redirect(redirect_url, code=303)


@app.route('/auth_team', methods=['POST'])
def auth_team():
    """Log into a team with its password."""
    name = request.form.get('name', '')
    password = request.form.get('password', '')
    team = Team.query.filter(func.lower(Team.name) == name.lower()).first()

    if team is None:
        flash('No team exists with that name.', 'danger')
        return redirect(url_for('login_page'), code=303)
    if not safe_str_cmp(password, team.password):
        flash('Incorrect team password.', 'danger')
        return redirect(url_for('login_page'), code=303)

    session['team'] = team.id
    flash('You are now logged in as %s.' % team.name, 'success')

    redirect_url = request.args.get('next')
    if not redirect_url or not is_safe_url(redirect_url):
        redirect_url = url_for('team_page', id=team.id)
    return redirect(redirect_url, code=303)


@app.route('/logout/')
@require_auth
def logout():
    """Clear the session, and redirect to home."""
    ensure_csrf(request.args.get('token'))
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home_page'), code=303)


@app.route('/passwords.zip')
def snoopin():
    return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ', code=303)


@app.route('/flags', methods=['POST'])
@require_auth
def submit_flag():
    """Attempt to submit a flag, and redirect to the flag page."""
    flag = request.form.get('flag', '')

    # Deliver swift justice
    if flag == 'V375BrzPaT':
        return snoopin()

    flag_hash = sha256(flag.encode('utf-8')).hexdigest()
    db_flag = Flag.query.filter_by(hash=flag_hash).first()
    team = Team.query.filter_by(id=session['team']).first()

    if db_flag is None:
        flash('Sorry, the flag you entered is not correct.', 'danger')
    elif db_flag.level in team.levels:
        flash('You\'ve already entered that flag.', 'warning')
    elif db.session.query(Level).filter(Level.category == db_flag.level.category) \
            .filter(Level.level < db_flag.level.level) \
            .filter(~Level.teams.any(id=team.id)).count() > 0:
        flash('You must complete all previous challenges first!', 'danger')
    else:
        team.levels.append(db_flag.level)
        team.points += db_flag.level.points
        team.last_flag = func.now()
        db.session.add(team)
        db.session.commit()
        flash('Correct! You have earned {0:d} points for your team.'
              .format(db_flag.level.points), 'success')

    return redirect(url_for('flag_page'), code=303)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', '5000')))
