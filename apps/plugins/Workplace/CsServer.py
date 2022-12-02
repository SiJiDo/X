# -*- encoding: utf-8 -*-
from flask import render_template, request
from apps import db
from hashlib import md5
import random
import os
import subprocess
from multiprocessing import Process

from apps.plugins.models import AttackServer
from apps.utils import get_segment,queryToDict,get_list,get_now_ip


MODLE_NAME = "CsServer"
FILEPATH = os.path.dirname(__file__) + "/../../../" +"tools/CsServer/cs42/"
CHINANAME = "Cobaltstrike模块"

#xx模块
def run():
    # 这里写逻辑
    query = AttackServer.query.filter(AttackServer.model == "CsServer").first()
    attackServer_cs = queryToDict(query)
    now_ip = get_now_ip(attackServer_cs['id'])
    query = AttackServer.query.filter(AttackServer.model == "FileWeb").first()
    httpport = queryToDict(query)
    httpport = httpport['serverport']


    action = request.args.get('action')
    port = request.args.get('port')

    if(action == "open"):
        Csserver_open(attackServer_cs, now_ip, port)
    
    if(action == "close"):
        Csserver_close(attackServer_cs)

    query = AttackServer.query.filter(AttackServer.model == "CsServer").first()
    attackServer_cs = queryToDict(query)

    #展示服务
    dic = {"now_ip" : now_ip,
        "httpport": httpport,
        "cspassword": attackServer_cs["serverprocess"],
        "csport": attackServer_cs["serverport"],
        "id": attackServer_cs["id"],

    }
    #初始化菜单栏
    return render_template('plugins/Cs.html', form=dic, segment=get_segment(request), attacklist = get_list())

#打开CS服务
def Csserver_open(attackServer_cs, now_ip, port):
    os.chdir(FILEPATH)
    if(port == "" or port == None):
        port = random.randint(40000,41000)
    #正式使用
    cmd = "sed -i 's/-Dcobaltstrike.server_port=.*/-Dcobaltstrike.server_port={} -Djavax.net.ssl.keyStore=.\/cobaltstrike.store -Djavax.net.ssl.keyStorePassword=123456 -server -XX:+AggressiveHeap -XX:+UseParallelGC -classpath .\/cobaltstrike.jar server.TeamServer $*/g' teamserver ".format(str(port))
    #mac 使用下面命令
    #cmd = "gsed -i 's/-Dcobaltstrike.server_port=.*/-Dcobaltstrike.server_port={} -Djavax.net.ssl.keyStore=.\/cobaltstrike.store -Djavax.net.ssl.keyStorePassword=123456 -server -XX:+AggressiveHeap -XX:+UseParallelGC -classpath .\/cobaltstrike.jar server.TeamServer $*/g' teamserver ".format(str(port))

    password = random.randint(20000000000,30000000000)
    password = md5(str(password).encode(encoding='UTF-8')).hexdigest()[:16]

    cmd2 = 'nohup ./teamserver {} {} ./service_cobaltstrike.profile &'.format(str(now_ip),str(password))
    try:
        os.system(cmd)
        os.system(cmd2)

        attackServer_cs['serverprocess'] = str(password)
        attackServer_cs['serverport'] = str(port)
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_cs["id"]).update(attackServer_cs)
        db.session.commit()
    except Exception as e:
        print(e)
    return

#关闭CS服务
def Csserver_close(attackServer_cs):
    attackServer_cs["serverprocess"] = "NONE"
    attackServer_cs["serverport"] = "0"
    db.session.query(AttackServer).filter(AttackServer.id == attackServer_cs["id"]).update(attackServer_cs)
    db.session.commit()
    os.system("ps -ef |grep teamserver |awk '{print $2}'|xargs kill -9")
    os.system("ps -ef |grep cobaltstrike |awk '{print $2}'|xargs kill -9")
    return