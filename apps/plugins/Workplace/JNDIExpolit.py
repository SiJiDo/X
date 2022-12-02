# -*- encoding: utf-8 -*-
from flask import render_template, request, flash
from apps import db
import random
import os
import subprocess
from multiprocessing import Process

from apps.plugins.models import AttackServer
from apps.utils import get_segment,queryToDict,get_list,get_now_ip,CheckPortSuccess


MODLE_NAME = "JNDIExpolit"
FILEPATH = os.path.dirname(__file__) + "/../../../" + "tools/JNDIExploit/"
CHINANAME = "JNDIExpolit模块"

#xx模块
def run():
    action = request.args.get('action')
    ldapport = request.args.get('ldapport')
    httpport = request.args.get('httpport')

    query = AttackServer.query.filter(AttackServer.model == "JNDIExpolit").first()
    attackServer_Jndi = queryToDict(query)
    now_ip = get_now_ip(attackServer_Jndi['id'])
    attackServer_Jndi['serverhost'] = now_ip
    
    #打开服务
    if(action == "open" and request.method == "GET"):
        #已经开放，不重复开放
        if(attackServer_Jndi['serverport'] != '0' and attackServer_Jndi['serverport'] != None):
            print("端口已开放")
            return render_template('plugins/JNDIServer.html',form={"attackServer_Jndi": attackServer_Jndi, "ldapport": "", "httpport":""}, segment=get_segment(request), attacklist = get_list())

        #开放在随机端口
        if((ldapport == None or ldapport == "" or ldapport == 0) and (httpport == None or httpport == "" or httpport == 0) ):
            #随机端口
            ldapport = random.randint(20000,21000)
            httpport = random.randint(21001,22000)
            if(CheckPortSuccess(ldapport) and CheckPortSuccess(httpport)):
                attackServer_Jndi['serverport'] = str(ldapport) + "," + str(httpport)
            else:
                print("端口冲突请重试")
                flash("端口冲突请重试")
                return render_template('plugins/JNDIServer.html',form={"attackServer_Jndi": attackServer_Jndi, "ldapport": "", "httpport":""}, segment=get_segment(request), attacklist = get_list())


        #随机ldap服务端口
        elif((ldapport == None or ldapport == "" or ldapport == 0) and (httpport != None or httpport != "" or httpport != 0) ):
            #随机端口
            ldapport = random.randint(20000,21000)
            if(CheckPortSuccess(ldapport) and CheckPortSuccess(httpport)):
                attackServer_Jndi['serverport'] = str(ldapport) + "," + str(httpport)
            else:
                print("端口冲突请重试")
                flash("端口冲突请重试")
                return render_template('plugins/JNDIServer.html',form={"attackServer_Jndi": attackServer_Jndi, "ldapport": "", "httpport":""}, segment=get_segment(request), attacklist = get_list())


        #随机http服务端口
        elif((ldapport != None or ldapport != "" or ldapport != 0) and (httpport == None or httpport == "" or httpport == 0) ):
            #随机端口
            httpport = random.randint(20000,21000)
            if(CheckPortSuccess(ldapport) and CheckPortSuccess(httpport)):
                attackServer_Jndi['serverport'] = str(ldapport) + "," + str(httpport)
            else:
                print("端口冲突请重试")
                flash("端口冲突请重试")
                return render_template('plugins/JNDIServer.html',form={"attackServer_Jndi": attackServer_Jndi, "ldapport": "", "httpport":""}, segment=get_segment(request), attacklist = get_list())


        #开放在指定端口
        else:
            try:
                if(CheckPortSuccess(ldapport) and CheckPortSuccess(httpport)):
                    attackServer_Jndi['serverport'] = str(ldapport) + "," + str(httpport)
                else:
                    print("端口冲突请重试")
                    flash("端口冲突请重试")
                    return render_template('plugins/JNDIServer.html',form={"attackServer_Jndi": attackServer_Jndi, "ldapport": "", "httpport":""}, segment=get_segment(request), attacklist = get_list())

            except Exception as e:
                print(e)

        p = Process(target=JDNIserver_open,args=("127.0.0.1", ldapport, httpport))
        #开启子进程，开启服务
        p.start()
        attackServer_Jndi['serverprocess'] = p.pid
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_Jndi["id"]).update(attackServer_Jndi)
        db.session.commit()

    #关闭服务
    if(action == "close" and request.method == "GET"):
        if(attackServer_Jndi['serverport'] == '0' or attackServer_Jndi['serverport'] == None):
            print("端口已关闭") 
            return render_template('plugins/JNDIServer.html',form={"attackServer_Jndi": attackServer_Jndi,}, segment=get_segment(request), attacklist = get_list())

        JNDIserver_close()
        attackServer_Jndi["serverprocess"] = "NONE"
        attackServer_Jndi["serverport"] = "0"
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_Jndi["id"]).update(attackServer_Jndi)
        db.session.commit()

    try:
    #展示服务
        dic = {
            "attackServer_Jndi": attackServer_Jndi,
            "ldapport": attackServer_Jndi["serverport"].split(",")[0] if attackServer_Jndi["serverport"] != "0" else "",
            "httpport": attackServer_Jndi["serverport"].split(",")[1] if attackServer_Jndi["serverport"] != "0" else "",
        }
    except:
        dic = {
        "attackServer_Jndi": attackServer_Jndi,
        "ldapport":  "",
        "httpport":  "",
    }
    #初始化菜单栏    
    return render_template('plugins/JNDIServer.html', form=dic, segment=get_segment(request), attacklist = get_list())

#打开JNDI服务
def JDNIserver_open(now_ip, ldapport, httpport):
    os.chdir(FILEPATH)
    cmd = 'nohup java -jar JNDIExploit.jar -i {} -l {} -p {} &'.format(str(now_ip),str(int(ldapport)),str(int(httpport)))
    try:
        os.system(cmd)
    except Exception as e:
        print(e)
    return 

#关闭JNDI服务
def JNDIserver_close():
    os.system("ps -ef |grep JNDIExploit.jar |awk '{print $2}'|xargs kill -9")
    return