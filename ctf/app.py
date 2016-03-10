from flask import Flask, render_template
from werkzeug.exceptions import HTTPException, InternalServerError
from . import __name__ as package_name
from .models import db
from .routes import bp
import os


def create_app():
    app = Flask(package_name)

    app.config['END_TIME_UTC'] = os.environ.get('END_TIME_UTC')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'not secure brah')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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

    app.register_blueprint(bp)

    return app
