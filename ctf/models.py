from .ext import db
from sqlalchemy.orm import column_property


invite_table = \
    db.Table('invites', db.Model.metadata,
             db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
             db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
             )


class Solve(db.Model):
    __tablename__ = 'solve'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'),
                             primary_key=True)
    earned_on = db.Column(db.DateTime, server_default=db.func.now())


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(60))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', backref='users')
    invites = db.relationship('Team', secondary=invite_table)


class Challenge(db.Model):
    __tablename__ = "challenge"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(123))
    points = db.Column(db.Integer)
    fleg_hash = db.Column(db.String(128), unique=True)
    teams_solved = db.relationship('Team', secondary='solve',
                                   backref='challenge', collection_class=set)
    prerequisite_id = db.Column(db.Integer, db.ForeignKey('challenge.id'))
    prerequisites = db.relationship('Challenge', collection_class=set)
    resources = db.relationship('Resource', backref='challenge')

    def chal_info(self):
        return {"id": self.id,
                "title": self.title,
                "description": self.description,
                "category": self.category,
                "points": self.points,
                "resources": [r.name for r in self.resources]}


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    invited = db.relationship('User', secondary=invite_table)
    challenges = db.relationship('Challenge', secondary='solve',
                                 backref='team', collection_class=set)

    score = column_property(
        db.select([db.func.coalesce(db.func.sum(Challenge.points), 0)])
        .select_from(db.join(Solve, Challenge,
                             Solve.challenge_id == Challenge.id))
        .where(Solve.team_id == id),
        deferred=True,
        group='scores',
    )

    last_solve = column_property(
        db.select([db.func.max(Solve.earned_on)])
        .select_from(Solve).where(Solve.team_id == id),
        deferred=True,
        group='scores',
    )


class Resource(db.Model):
    __tablename__ = "resource"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    path = db.Column(db.String(128))
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'))
