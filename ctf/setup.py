from flask import current_app as app
from sqlalchemy.exc import IntegrityError
from .ext import db
from os import path
from .models import Challenge, Resource
from .core import hash_fleg
import json


def build_problem_options(problem_config, category):
    problem = dict(problem_config)
    del problem['fleg']
    del problem['resources']

    problem['fleg_hash'] = hash_fleg(problem_config['fleg'])
    problem['category'] = category

    # We put this first to avoid circular dependancies
    prereqs = set()
    if len(problem["prerequisites"]) > 0:
        prereqs = Challenge.query.filter(
            Challenge.title.in_(problem["prerequisites"])).all()
        if len(problem["prerequisites"]) != len(prereqs):
            raise ValueError("Prerequisite mismatch, %s" %
                             problem["title"])
    problem['prerequisites'] = set(prereqs)

    return problem


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
                problem_dict = build_problem_options(problem, c)
                challenge = Challenge(**problem_dict)
                db.session.add(challenge)

                for f in problem["resources"]:
                    file_path = path.join(chal_path, c)
                    resource = Resource(name=f,
                                        path=file_path,
                                        challenge=challenge)
                    db.session.add(resource)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    challenge = Challenge.query.filter_by(
                            title=problem['title'])
                    problem_dict.update({'id': challenge.first().id})
                    challenge.update(problem_dict)
                    db.session.commit()
