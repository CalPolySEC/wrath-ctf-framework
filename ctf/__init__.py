import json
import os
import flask
import redis
from werkzeug import exceptions
from . import api, core, frontend, ext, setup
from .models import db


def create_app():
    app = flask.Flask(__name__)
    config_file = "./ctf.json"

    if 'CTF_CONFIG' in os.environ:
        config_file = os.environ['CTF_CONFIG']

    try:
        config = open(config_file, 'r')
        app.config.update(json.load(config))
    except IOError:
        raise IOError("The CTF configuration file could not be found")
    except ValueError:
        raise ValueError("The CTF configuration file was malformed")

    app.redis = redis.StrictRedis()

    # Setup extensions
    ext.db.init_app(app)
    ext.csrf.init_app(app)

    @app.before_first_request
    def create_db():
        db.create_all()
        setup.build_challenges()

    @app.context_processor
    def inject_jinja_globals():
        """The authed flag should NOT be used to secure access control.

        The aim of the 'authed' global is simply better link rendering in
        templates.
        """
        return {'authed': 'key' in flask.session,
                'name': core.get_name()}

    def handle_error(exc):
        if not isinstance(exc, exceptions.HTTPException):
            exc = exceptions.InternalServerError()
        return flask.render_template('error.html', code=exc.code), exc.code

    for code in exceptions.default_exceptions.keys():
        app.register_error_handler(code, handle_error)

    app.register_blueprint(frontend.bp)
    app.register_blueprint(api.bp, url_prefix='/api')

    return app
