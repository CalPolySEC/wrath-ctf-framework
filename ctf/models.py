from .ext import db


invite_table = \
    db.Table('invites', db.Model.metadata,
             db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
             db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
             )


CleverName = \
    db.Table('clever_name', db.Model.metadata,
             db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
             db.Column('challenge_id', db.Integer,
                       db.ForeignKey('challenge.id')),
             db.Column('earned_on', db.DateTime, server_default=db.func.now())
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
    challenges = db.relationship('Challenge', secondary=CleverName,
                                 backref='team', collection_class=set)


class Challenge(db.Model):
    __tablename__ = "challenge"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(123))
    points = db.Column(db.Integer)
    fleg_hash = db.Column(db.String(128), unique=True)
    teams_solved = db.relationship('Team', secondary=CleverName,
                                   backref='challenge', collection_class=set)

    def chal_info(self):
        return {"id": self.id,
                "title": self.title,
                "description": self.description,
                "category": self.category,
                "points": self.points}
