from flask import Flask, request, session, redirect, render_template, url_for,\
                  flash
from flask_sqlalchemy import SQLAlchemy
from getwords import getwords
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound


app = Flask(__name__)
db = SQLAlchemy(app)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/teams', methods=['POST'])
def new_team():
    """Create a new team, with a generated password."""
    name = request.form.get('name', '')
    if not name:
        flash('You must supply a team name', 'danger')
        return redirect(url_for('login'), code=303)
    if Team.query.filter(func.lower(Team.name) == func.lower(name)).count() > 0:
        flash('That team name is taken.', 'danger')
        return redirect(url_for('login'), code=303)

    password = getwords()
    team = Team(name=name, password=password)
    db.session.add(team)
    db.session.commit()
    session['team'] = team.id
    flash('Team successfully created.', 'success')
    return redirect(url_for('get_team', id=team.id), code=303)


@app.route('/auth_team', methods=['POST'])
def auth_team():
    name = request.form.get('name', '')
    password = request.form.get('password', '')
    team = Team.query.filter(func.lower(Team.name) == func.lower(name)).first()

    if not password:
        flash('You must supply a password.', 'danger')
        return redirect(url_for('login'), code=303)
    if team is None:
        flash('No team exists with that name.', 'danger')
        return redirect(url_for('login'), code=303)
    if password != team.password:
        flash('Incorrect team password.', 'danger')
        return redirect(url_for('login'), code=303)

    session['team'] = team.id
    return redirect(url_for('get_team', id=team.id), code=303)


@app.route('/teams/<int:id>')
def get_team(id):
    team = Team.query.filter_by(id=id).first()
    if team is None:
        raise NotFound()
    return render_template('team.html', team=team)


@app.route('/submit')
def submit_flag():
    return render_template('submit.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'not secure brah'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.run(debug=True)
