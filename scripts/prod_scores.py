"""Build the production database"""

from Crypto.Cipher import AES
import hashlib
import json
import subprocess

# This here is a hack
import sys
sys.path.extend('..')
from app import db, Category, Flag, Team


def load_passwords(in_file):
    with subprocess.Popen(['/usr/bin/openssl', 'enc', '-d', '-aes-256-cbc'],
        stdin=in_file, stdout=subprocess.PIPE) as proc:
        for p in proc.stdout:
            yield hashlib.sha256(p.strip()).hexdigest()


def main(argv):
    if len(argv) < 4 :
        sys.stderr.write('Usage: python prod_scores.py ORDER SCORES PASSWORDS\n')
        return 1
    with open(argv[2], 'r') as score_file:
        scores = json.load(score_file)
        wargame = scores['wargame']
        points = sorted([(int(k), v) for k, v in scores['PointsByLevel'].items()])
    with open(argv[3], 'rb') as pw_file:
        passwords = load_passwords(pw_file)
        db.create_all()
        cat = Category(name=wargame, order=int(argv[1]))
        db.session.add(cat)
        for level, flag_hash in enumerate(passwords):
            flag = Flag(hash=flag_hash, level=level, category=cat, points=points[level][1])
            db.session.add(flag)
        db.session.commit()
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
