from datetime import datetime
from flask import Blueprint, current_app, request, session, abort, redirect, \
                  render_template, url_for, flash
from flask.ext.wtf.csrf import validate_csrf
from functools import wraps
from hashlib import sha256
from sqlalchemy import func
from werkzeug.exceptions import HTTPException, BadRequest, NotFound, InternalServerError
from werkzeug.security import safe_str_cmp
from . import ctf
from .forms import NewTeamForm, LoginForm
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
    teams = ctf.get_teams()
    return render_template('home.html', teams=teams)


@bp.route('/submit/')
@require_auth
def flag_page():
    return render_template('submit.html')


@bp.route('/teams/<int:id>/')
def team_page(id):
    """Get the page for a specific team."""
    team = ctf.get_team(id)
    if not team:
        abort(404)
    categories = ctf.get_categories()
    return render_template('team.html', team=team, categories=categories)


@bp.route('/login/', methods=['GET', 'POST'])
def login_page():
    """Log into a team with its password."""
    login_form = LoginForm(prefix='login')
    create_form = NewTeamForm(prefix='create')
    team = None

    if login_form.validate_on_submit() and login_form.submit.data:
        team = ctf.login_team(login_form.name.data, login_form.password.data)
        if team:
            flash('You are now logged in as %s.' % team.name, 'success')
        else:
            flash('Incorrect team name or password.', 'danger')
    elif create_form.validate_on_submit() and create_form.submit.data:
        team = ctf.create_team(create_form.name.data)
        if team:
            flash('Team successfully created.', 'success')
        else:
            flash('That team name is taken.', 'danger')

    if team:
        session['team'] = team.id
        session.permanent = True
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
    fleg = request.form.get('flag', '')
    # Deliver swift justice
    if fleg == 'V375BrzPaT':
        return snoopin()

    db_flag, err_msg = ctf.add_flag(fleg, session['team'])
    if err_msg:
        flash(err_msg, 'danger')
    else:
        flash('Correct! You have earned {0:d} points for your team.'
              .format(db_flag.level.points), 'success')

    return redirect(url_for('.flag_page'), code=303)
