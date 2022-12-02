# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request,flash, redirect, url_for
from flask_login import login_required,current_user,logout_user
from jinja2 import TemplateNotFound
from apps.plugins.models import AttackServer
from apps.authentication.util import hash_pass,verify_pass
from apps.authentication.models import Users
from apps import db
from apps import utils
import random
from hashlib import md5


@blueprint.route('/index')
@login_required
def index():

    attackserver_query = db.session.query(AttackServer).all()
    if(attackserver_query == []):
        attackserver_query = {}
    else:
        attackserver_query = utils.queryToDict(attackserver_query)
    
    dic = {
        "attackserver_query": attackserver_query
    }

    return render_template('home/index.html', segment='index', form=dic, attacklist = utils.get_list())


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template,form={} , segment=segment, attacklist = utils.get_list())

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500

@blueprint.route('/userlist')
@login_required
def userconfig():
    isadmin = False
    
    query = db.session.query(Users).filter(Users.username == str(current_user)).first()
    nowuser = utils.queryToDict(query)
    if nowuser['admin'] == 1:
        isadmin = True

    if(request.args.get("action") == "reset"):
        id = request.args.get("uid")
        if(id != "1"):
            password = "Xx145213."
            hash_password = hash_pass(password)
            db.session.query(Users).filter(Users.id == id).update({"password":hash_password})
            db.session.commit()
            flash("密码重置为:" + password)

    if(request.args.get("action") == "delete"):
        id = request.args.get("uid")
        if(id != "1"):
            db.session.query(Users).filter(Users.id == id).delete()
            db.session.commit()
    

    query = db.session.query(Users).all()
    users = utils.queryToDict(query)
    for i in users:
        print(i)
    dic = {
        "userinfo" : users,
        "isadmin": isadmin
    }
    return render_template('home/userlist.html', segment='userlist', form=dic, attacklist = utils.get_list())

@blueprint.route('/AddUser', methods=['GET', 'POST'])
@login_required
def AddUser():
    query = db.session.query(Users).filter(Users.username == str(current_user)).first()
    nowuser = utils.queryToDict(query)
    if nowuser['admin'] != 1:
        return render_template('home/page500.html', segment='AddUser', form={}, attacklist = utils.get_list()) 

    if(request.method=="POST"):
        data = request.form.to_dict()
        username = data['username']
        try:
            print(data['admin'])
            data['admin'] = 1
        except Exception as e:
            data['admin'] = 0
        query = db.session.query(Users).filter(Users.username == username)
        if(query.count() > 0):
            flash("用户存在请更换用户名注册")
        else:
            user = Users(
                data['username'],
                data['password'],
                data['admin'],
                data['dec'],
            )

            db.session.add(user)
            db.session.commit()
            
    return render_template('home/adduser.html', segment='AddUser', form={}, attacklist = utils.get_list())

@blueprint.route('/ChangePass', methods=['GET', 'POST'])
@login_required
def ChangePass():
    if(request.method=="POST"):
        data = request.form.to_dict()
        if data['newpassword2'] != data['newpassword']:
            flash("两次输入新密码不一样")
        else:
            query = db.session.query(Users).filter(Users.username == str(current_user)).first()
            user = utils.queryToDict(query)
            print(user)
            if verify_pass(data['oldpassword'],user['password']):
                user['password'] = hash_pass(data['newpassword'])
                db.session.query(Users).filter(Users.username == str(current_user)).update(user)
                db.session.commit()
                logout_user()
                return redirect(url_for('authentication_blueprint.login')) 
            else:
                flash("原密码不正确")
    return render_template('home/changepassword.html', segment='ChangePass', form={}, attacklist = utils.get_list())

# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
