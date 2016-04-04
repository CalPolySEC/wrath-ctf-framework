from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()

team_level_table = \
    db.Table('team_levels', db.Model.metadata,
             db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
             db.Column('level_id', db.Integer, db.ForeignKey('level.id'))
             )

invite_table = \
    db.Table('invites', db.Model.metadata,
             db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
             db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
             )


class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64))
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'))
    level = db.relationship('Level')


class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer)
    level = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    teams = db.relationship('Team', secondary=team_level_table)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(20))
    levels = db.relationship('Level', backref='category')
    enforce = db.Column(db.Boolean())


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(60))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', backref='users')
    invites = db.relationship('Team', secondary=invite_table)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    points = db.Column(db.Integer, default=0)
    levels = db.relationship('Level', secondary=team_level_table)
    last_flag = db.Column(db.DateTime, server_default=db.func.now())
    invited = db.relationship('User', secondary=invite_table)
