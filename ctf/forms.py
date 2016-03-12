from flask.ext.wtf import Form
from wtforms import validators, StringField, PasswordField, SubmitField


class NewTeamForm(Form):
    name = StringField('Team name', validators=[validators.Required()])
    submit = SubmitField('Create team')


class LoginForm(Form):
    name = StringField('Team name', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Join team')
