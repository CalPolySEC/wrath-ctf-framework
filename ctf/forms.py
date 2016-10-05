from flask_wtf import Form
from wtforms import validators, StringField, PasswordField, SubmitField


class CreateForm(Form):
    username = StringField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Login')


class LoginForm(Form):
    username = StringField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Login')


class TeamForm(Form):
    name = StringField('Name', validators=[validators.Required()])
    submit = SubmitField('Create Team')


class SubmitForm(Form):
    fleg = StringField('Flag', validators=[validators.Required()])
    submit = SubmitField('Go!')


class InviteForm(Form):
    name = StringField('Name', validators=[validators.Required()])
    submit = SubmitField('Invite')


class JoinForm(Form):
    join_name = StringField('Name', validators=[validators.Required()])
    submit = SubmitField('Join Team')
