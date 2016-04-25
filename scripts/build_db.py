"""Build a temporary database"""

import hashlib
# This here is a hack
import sys
sys.path.extend('..') # jesus
from ctf.app import create_app
from ctf.models import db, Category, Fleg, Level, Team

TEST_CATEGORIES = [('Bandit', 26), ('Leviathan', 7), ('Lock Picking', 0), ('Teardown', 0)]

def main():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    with app.app_context():
        db.create_all()
        for index, (cat, levels) in enumerate(TEST_CATEGORIES):
            c = Category(name=cat, order=index)
            db.session.add(c)
            for level in range(levels + 1):
                lev = Level(category=c, level=level, points=10)
                fleg = Fleg(hash=hashlib.sha256(b'%s %d' % (cat.encode(), level)).hexdigest(), level=lev)
                db.session.add(lev)
                db.session.add(fleg)
        db.session.commit()
    return 0

if __name__ == '__main__':
    sys.exit(main())
