from .ext import db


invite_table = \
    db.Table('invites', db.Model.metadata,
             db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
             db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
             )


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(60))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', backref='users')
    invites = db.relationship('Team', secondary=invite_table)


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    points = db.Column(db.Integer, default=0)
    last_fleg = db.Column(db.DateTime, server_default=db.func.now())
    invited = db.relationship('User', secondary=invite_table)


class Fleg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='flegs')
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', backref='flegs')
    points = db.Column(db.Integer)
    earned_on = db.Column(db.DateTime, server_default=db.func.now())

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    description = db.Column(db.Text)
    fleg_id = db.Column(db.Integer, db.ForeignKey('fleg.id')) 
    fleg = db.relationship('Fleg')
