# -*- encoding: utf-8 -*-
from curses import keyname
from email.policy import default
from enum import unique
from apps import db
from sqlalchemy.sql.sqltypes import Boolean


# class SystemValue(db.Model):

#     __tablename__ = 'SystemValue'

#     id            = db.Column(db.Integer, autoincrement=True, primary_key=True)
#     key           = db.Column(db.String(128), unique = True)
#     status        = db.Column(Boolean, default = False)

