"""Build a temporary database"""

import hashlib
# This here is a hack
import sys
sys.path.extend('..')
from ctf_app import app, db, Category, Flag, Team

def main():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    db.create_all()
    for cat, levels in (('Bandit', 26), ('Leviathan', 7), ('Lock Picking', 0), ('Teardown', 0)):
        c = Category(name=cat)
        db.session.add(c)
        for level in range(levels + 1):
            flag = Flag(hash=hashlib.sha256(b'%s %d' % (cat.encode(), levels)).hexdigest(), level=level, category=c)
            db.session.add(flag)
    db.session.commit()
    return 0

if __name__ == '__main__':
    sys.exit(main())
