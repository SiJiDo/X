# -*- encoding: utf-8 -*-
from flask import  request
from apps.plugins.models import AttackServer
from apps import db
from apps.plugins import blueprint
from apps import utils
from flask_login import login_required
from importlib import import_module

#AttackServer模块
@blueprint.route('/AttackServer', methods=['GET', 'POST'])
@login_required
def route_webfile():
    id = request.args.get("id")
    query = db.session.query(AttackServer).filter(AttackServer.id == id).first()
    dict = utils.queryToDict(query)
    module = import_module('apps.plugins.Workplace.{}'.format(dict['model']))
    return module.run()