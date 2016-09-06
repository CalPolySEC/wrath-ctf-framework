from flask import current_app as app
from .ext import db
from os import path
from .models import Challenge
from core import hash_fleg
import json


def build_challenges():
    chal_path = path.join(app.root_path, "../",
                          app.config['CTF']['challenges'])
    categories = app.config['CTF']['categories']
    for c in categories:
        problem_config = path.join(chal_path, c, "problems.json")
        with open(problem_config, 'r') as config_file:
            try:
                config = json.load(config_file)
            except ValueError:
                raise ValueError("%s was malformed" % config_file)
            for problem in config["problems"]:
                challenge = Challenge(title=problem["title"],
                                      description=problem["description"],
                                      category=c,
                                      points=problem["points"],
                                      fleg_hash=hash_fleg(problem["fleg"]))
                try:
                    db.session.add(challenge)
                    db.session.commit()
                except:
                    print "Something went wrong with challenge %s, skipping" \
                     % problem["title"]
                    
