"""Build a temporary database"""

import hashlib
# This here is a hack
import sys
sys.path.extend('..') # jesus
from app import app, db, Category, Flag, Team

TEST_CATEGORIES = [('Bandit', 26), ('Leviathan', 7), ('Lock Picking', 0), ('Teardown', 0)]

def main():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    db.create_all()
    for index, (cat, levels) in enumerate(TEST_CATEGORIES):
        c = Category(name=cat, order=index)
        db.session.add(c)
        for level in range(levels + 1):
            flag = Flag(hash=hashlib.sha256(b'%s %d' % (cat.encode(), level)).hexdigest(), level=level, category=c, points=10)
            db.session.add(flag)
    db.session.commit()
    return 0

if __name__ == '__main__':
    sys.exit(main())
