from flask import Flask, render_template
from werkzeug import exceptions
from . import api, frontend, ext
from .models import db
import os
import redis


def create_app():
    app = Flask(__name__)

    app.config['END_TIME_UTC'] = os.environ.get('END_TIME_UTC')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'not secure brah')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                           'sqlite:///test.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.redis = redis.StrictRedis()

    # Setup extensions
    ext.db.init_app(app)
    ext.csrf.init_app(app)

    @app.before_first_request
    def create_db():
        db.create_all()

    def handle_error(exc):
        if not isinstance(exc, exceptions.HTTPException):
            exc = exceptions.InternalServerError()
        return render_template('error.html', error=exc), exc.code

    for code in exceptions.default_exceptions.keys():
        app.register_error_handler(code, handle_error)

    app.register_blueprint(frontend.bp)
    app.register_blueprint(api.bp, url_prefix='/api')

    return app
