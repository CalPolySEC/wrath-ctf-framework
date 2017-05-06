from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField, SubmitField


class CreateForm(FlaskForm):
    username = StringField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Login')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Login')


class TeamForm(FlaskForm):
    name = StringField('Name', validators=[validators.Required()])
    submit = SubmitField('Create Team')


class SubmitForm(FlaskForm):
    fleg = StringField('Flag', validators=[validators.Required()])
    submit = SubmitField('Go!')


class InviteForm(FlaskForm):
    name = StringField('Name', validators=[validators.Required()])
    submit = SubmitField('Invite')


class JoinForm(FlaskForm):
    join_name = StringField('Name', validators=[validators.Required()])
    submit = SubmitField('Join Team')
