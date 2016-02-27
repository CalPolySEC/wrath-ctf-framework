"""Build the production database"""

from Crypto.Cipher import AES
import hashlib
import json
import subprocess

# This here is a hack
import sys
sys.path.extend('..')
from app import db, Category, Flag, Level, Team


def load_passwords(in_file):
    with subprocess.Popen(['/usr/bin/openssl', 'enc', '-d', '-aes-256-cbc'],
        stdin=in_file, stdout=subprocess.PIPE) as proc:
        for i, p in enumerate(proc.stdout):
            p = p.strip()
            if b' ' in p:
                lev, fleg = p.split(' ', 1)
            else:
                lev = i
                fleg = p
            yield int(lev), hashlib.sha256(fleg).hexdigest()


def main(argv):
    if len(argv) < 4 :
        sys.stderr.write('Usage: python prod_scores.py ORDER SCORES PASSWORDS\n')
        return 1
    with open(argv[2], 'r') as score_file:
        scores = json.load(score_file)
        wargame = scores['wargame']
        cat = Category(name=wargame, order=int(argv[1]), enforce=scores.get('enforce_order', False))
        levels = []
        for level, points in sorted([(int(k), v) for k, v in scores['PointsByLevel'].items()]):
            lev = Level(category=cat, level=level, points=points)
            levels.append(lev)
            db.session.add(lev)
    with open(argv[3], 'rb') as pw_file:
        passwords = load_passwords(pw_file)
        db.create_all()
        db.session.add(cat)
        for lev, flag_hash in passwords:
            flag = Flag(hash=flag_hash, level=levels[lev])
            db.session.add(flag)
        db.session.commit()
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
