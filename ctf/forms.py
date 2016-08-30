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
