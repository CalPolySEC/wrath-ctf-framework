# -*- coding: utf-8 -*-
"""All our extensions"""
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import CsrfProtect


csrf = CsrfProtect()
db = SQLAlchemy()
