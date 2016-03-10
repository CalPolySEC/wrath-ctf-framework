from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()

association_table = db.Table('team_levels', db.Model.metadata,
    db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
    db.Column('level_id', db.Integer, db.ForeignKey('level.id'))
)


class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64))
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'))
    level = db.relationship("Level")


class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer)
    level = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    teams = db.relationship('Team', secondary=association_table)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(20))
    levels = db.relationship('Level', backref='category')
    enforce = db.Column(db.Boolean())


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    points = db.Column(db.Integer, default=0)
    levels = db.relationship('Level', secondary=association_table)
    last_flag = db.Column(db.DateTime, server_default=db.func.now())
