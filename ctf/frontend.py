from datetime import datetime
from flask import Blueprint, current_app, request, session, abort, redirect, \
                  g, render_template, url_for, flash
from flask.ext.wtf.csrf import validate_csrf
from functools import wraps
from sqlalchemy import func
from werkzeug.exceptions import HTTPException, BadRequest, NotFound, \
                                InternalServerError
from werkzeug.security import safe_str_cmp
from . import core
from .core import CtfException
from .forms import CreateForm, LoginForm
import os
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


bp = Blueprint('frontend', __name__)


def is_safe_url(url):
    """Determine whether a URL is safe for redirection."""
    u = urlparse(url)
    return u.scheme == '' and u.netloc == '' and u.path != request.path


@bp.after_request
def snoop_header(response):
    response.headers['X-Snoop-Options'] = 'nosnoop'
    return response


@bp.before_request
def check_user():
    g.user = None
    if 'key' in session:
        g.user = core.user_for_token(session['key'])


def ensure_user():
    if g.user is None:
        flash('You must be logged in to a team to do that.', 'danger')
        return redirect(url_for('.login'), next=request.path, code=303)
    return g.user


def ensure_team():
    user = ensure_user()
    team = core.team_for_user(user)
    if team is None:
        abort('You must be part of a team.', 'danger')
        return redirect(url_for('.home'), code=303)
    return user.team


@bp.route('/')
def home_page():
    teams = core.get_teams()
    return render_template('home.html', teams=teams)


@bp.route('/submit/')
def fleg_page():
    team = ensure_team()
    return render_template('submit.html')


@bp.route('/teams/<int:id>/')
def team_page(id):
    """Get the page for a specific team."""
    team = core.get_team(id)
    if not team:
        abort(404)
    categories = core.get_categories()
    return render_template('team.html', team=team, categories=categories)


def redirect_next(fallback, **kwargs):
    url = request.args.get('next')
    if not url or not is_safe_url(url):
        url = fallback
    return redirect(url, **kwargs)


@bp.route('/register/', methods=['GET', 'POST'])
def create_user():
    form = CreateForm()
    if form.validate_on_submit():
        try:
            user = core.create_user(form.username.data, form.password.data)
        except CtfException as exc:
            flash(exc.message, 'danger')
        else:
            key = core.create_session_key(user)
            session['key'] = key
            return redirect_next(fallback=url_for('.home_page'), code=303)
    return render_template('register.html', form=form)


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    """Log into a team with its password."""
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = core.login(form.username.data, form.password.data)
        except CtfException as exc:
            flash(exc.message, 'danger')
        else:
            key = core.create_session_key(user)
            session['key'] = key
            return redirect_next(fallback=url_for('.home_page'), code=303)
    return render_template('login.html', form=form)


@bp.route('/logout/')
def logout():
    """Clear the session, and redirect to home."""
    user = ensure_user()
    if not validate_csrf(request.args.get('token')):
        abort(400)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('.home_page'), code=303)


@bp.route('/passwords.zip')
def snoopin():
    return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ', code=303)


@bp.route('/flags', methods=['POST'])
def submit_fleg():
    """Attempt to submit a fleg, and redirect to the fleg page."""
    team = ensure_team()
    fleg = request.form.get('flag', '')
    # Deliver swift justice
    if fleg == 'V375BrzPaT':
        return snoopin()

    db_fleg, err_msg = core.add_fleg(fleg, session['team'])
    if db_fleg is None:
        flash(err_msg, 'danger')
    else:
        flash('Correct! You have earned {0:d} points for your team.'
              .format(db_fleg.level.points), 'success')

    return redirect(url_for('.fleg_page'), code=303)
