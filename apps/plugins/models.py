# -*- encoding: utf-8 -*-
from apps import db
from sqlalchemy.dialects.mysql import LONGTEXT


class WebFile(db.Model):

    __tablename__ = 'WebFile'

    id            = db.Column(db.Integer, autoincrement=True, primary_key=True)
    filepath      = db.Column(db.String(512))
    filename      = db.Column(db.String(256), unique=True)
    adduser       = db.Column(db.String(256))
    dec           = db.Column(db.String(256))

    def __init__(self,filepath,filename,adduser,dec):
        self.filename = filename
        self.filepath = filepath
        self.adduser = adduser
        self.dec = dec

class AttackServer(db.Model):

    __tablename__ = 'AttackServer'

    id            = db.Column(db.Integer, autoincrement=True, primary_key=True)
    model         = db.Column(db.String(256), unique=True)
    filepath      = db.Column(db.String(256))
    serverprocess = db.Column(db.String(1024))
    serverhost    = db.Column(db.String(256))
    serverport    = db.Column(db.String(256))
    chinaname     = db.Column(db.String(256))

    def __init__(self,model,filepath,serverprocess,serverhost,serverport,chinaname):
        self.model = model
        self.filepath = filepath
        self.serverprocess = serverprocess
        self.serverhost = serverhost
        self.serverport = serverport
        self.chinaname = chinaname