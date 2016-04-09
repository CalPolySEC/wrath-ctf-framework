from flask.ext.wtf import Form
from wtforms import validators, StringField, PasswordField, SubmitField


class CreateForm(Form):
    username = StringField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Login')


class LoginForm(Form):
    username = StringField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    submit = SubmitField('Login')
