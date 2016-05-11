# -*- coding: utf-8 -*-
"""All our extensions"""
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import CsrfProtect


csrf = CsrfProtect()
db = SQLAlchemy()
