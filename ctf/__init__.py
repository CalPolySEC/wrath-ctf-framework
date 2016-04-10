from flask import Flask, render_template
from flask.ext.wtf.csrf import CsrfProtect
from redis import StrictRedis
from werkzeug.exceptions import HTTPException, InternalServerError
from . import api, frontend
from .models import db
import os


def create_app():
    app = Flask(__name__)

    app.config['END_TIME_UTC'] = os.environ.get('END_TIME_UTC')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'not secure brah')
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                           'sqlite:///test.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.redis = StrictRedis()

    CsrfProtect(app)
    db.init_app(app)

    @app.before_first_request
    def create_db():
        db.create_all()

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(500)
    def handle_error(exc):
        if not isinstance(exc, HTTPException):
            exc = InternalServerError()
        return render_template('error.html', error=exc), exc.code

    app.register_blueprint(frontend.bp)
    app.register_blueprint(api.bp, url_prefix='/api')

    return app
