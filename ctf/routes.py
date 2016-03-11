from base64 import urlsafe_b64encode
from datetime import datetime
from flask import Blueprint, current_app, request, session, abort, redirect, \
                  render_template, url_for, flash
from flask.ext.wtf.csrf import validate_csrf
from functools import wraps
from hashlib import sha256
from sqlalchemy import func
from werkzeug.exceptions import HTTPException, BadRequest, NotFound, InternalServerError
from werkzeug.security import safe_str_cmp
from .forms import NewTeamForm, LoginForm
from .models import db, Team, Flag, Level, Category
from .getwords import getwords
import os
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


bp = Blueprint('routes', __name__)


def is_safe_url(url):
    """Determine whether a URL is safe for redirection."""
    u = urlparse(url)
    return u.scheme == '' and u.netloc == '' and u.path != request.path


@bp.after_request
def snoop_header(response):
    response.headers['X-Snoop-Options'] = 'nosnoop'
    return response


def require_auth(fn):
    """Redirect to the login page if the user is not authenticated."""
    @wraps(fn)
    def inner(*args, **kwargs):
        if 'team' not in session:
            flash('You must be logged in to a team to do that.', 'danger')
            return redirect(url_for('.login_page', next=request.path), code=303)
        return fn(*args, **kwargs)
    return inner


@bp.route('/')
def home_page():
    teams = Team.query.order_by(Team.points.desc(), Team.last_flag).all()
    return render_template('home.html', teams=teams)


@bp.route('/submit/')
@require_auth
def flag_page():
    return render_template('submit.html')


@bp.route('/teams/<int:id>/')
def team_page(id):
    """Get the page for a specific team."""
    team = Team.query.filter_by(id=id).first_or_404()
    cat_query = Category.query.order_by(Category.order.asc())
    categories = [(cat.name, cat.levels) for cat in cat_query]
    return render_template('team.html', team=team, categories=categories)


@bp.route('/login/', methods=['GET', 'POST'])
def login_page():
    """Log into a team with its password."""
    login_form = LoginForm(prefix='login')
    create_form = NewTeamForm(prefix='create')
    success = False
    formtype = request.args.get('type')

    if login_form.validate_on_submit() and login_form.submit.data:
        name = login_form.name.data
        password = login_form.password.data
        team = Team.query.filter(func.lower(Team.name) == name.lower()).first()

        if team is None:
            flash('No team exists with that name.', 'danger')
        elif  not safe_str_cmp(password, team.password):
            flash('Incorrect team password.', 'danger')
        else:
            session['team'] = team.id
            session.permanent = True
            flash('You are now logged in as %s.' % team.name, 'success')
            success = True

    elif create_form.validate_on_submit() and create_form.submit.data:
        name = create_form.name.data

        if Team.query.filter(func.lower(Team.name) == name.lower()).count():
            flash('That team name is taken.', 'danger')
        else:
            team = Team(name=name, password=getwords())
            db.session.add(team)
            db.session.commit()
            session['team'] = team.id
            flash('Team successfully created.', 'success')
            success = True

    if success:
        redirect_url = request.args.get('next')
        if not redirect_url or not is_safe_url(redirect_url):
            redirect_url = url_for('.team_page', id=team.id)
        return redirect(redirect_url, code=303)
    else:
        return render_template('login.html', create_form=create_form,
                               login_form=login_form)


@bp.route('/logout/')
@require_auth
def logout():
    """Clear the session, and redirect to home."""
    if not validate_csrf(request.args.get('token')):
        abort(400)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('.home_page'), code=303)


@bp.route('/passwords.zip')
def snoopin():
    return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ', code=303)


@bp.route('/flags', methods=['POST'])
@require_auth
def submit_flag():
    """Attempt to submit a flag, and redirect to the flag page."""
    flag = request.form.get('flag', '')

    # Deliver swift justice
    if flag == 'V375BrzPaT':
        return snoopin()

    end_time = current_app.config['END_TIME_UTC']
    if end_time and datetime.utcnow() > datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ'):
        flash('The competition has ended, sorry.', 'danger')
        return redirect(url_for('.flag_page'), code=303)

    flag_hash = sha256(flag.encode('utf-8')).hexdigest()
    db_flag = Flag.query.filter_by(hash=flag_hash).first()
    team = Team.query.filter_by(id=session['team']).first()

    if db_flag is None:
        flash('Sorry, the flag you entered is not correct.', 'danger')
    elif db_flag.level in team.levels:
        flash('You\'ve already entered that flag.', 'warning')
    elif db_flag.level.category.enforce and db.session.query(Level) \
            .filter(Level.category == db_flag.level.category) \
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

    return redirect(url_for('.flag_page'), code=303)
