# -*- encoding: utf-8 -*-
from flask import render_template, request, redirect, flash
from apps import db
import random
import os
import subprocess
from multiprocessing import Process
from flask_login import current_user

from apps.plugins.models import AttackServer
from apps.plugins.models import WebFile
from apps.utils import get_segment,queryToDict,get_list,get_now_ip, CheckPortSuccess


MODLE_NAME = "FileWeb"
FILEPATH =  os.path.dirname(__file__) + "/../../../" +"tools/FileWeb"
CHINANAME = "Web目录管理"

#FileWeb模块
def run():
    print(FILEPATH)
    port = request.args.get('webfile_port')
    action = request.args.get('action')

    query = AttackServer.query.filter(AttackServer.model == "FileWeb").first()
    attackServer_FileWeb = queryToDict(query)
    now_ip = get_now_ip(attackServer_FileWeb['id'])
    
    #展示数据
    dic = {
        "attackServer_FileWeb" : attackServer_FileWeb,
        "now_ip" : now_ip
    }

    #打开服务
    if(action == "open" and request.method == "GET"):
        #已经开放，不重复开放
        if(attackServer_FileWeb['serverport'] != '0' and attackServer_FileWeb['serverport'] != None):
            print("端口已开放")
            return render_template('plugins/FileWeb.html',form=dic, segment=get_segment(request), attacklist = get_list())

        #开放在随机端口
        if(port == None or port == "" or port == 0):
            #随机端口
            randport = random.randint(10000,11000)
            if(CheckPortSuccess(randport)):
                attackServer_FileWeb['serverport'] = str(randport)
            else:
                print("端口冲突请重试")
                flash("端口冲突请重试")
                return render_template('plugins/FileWeb.html',form=dic, segment=get_segment(request), attacklist = get_list())


        #开放在指定端口
        else:
            try:
                if(CheckPortSuccess(port)):
                    attackServer_FileWeb['serverport'] = str(port)
                else:
                     print("端口冲突请重试")
                     flash("端口冲突请重试")
                     return render_template('plugins/FileWeb.html',form=dic, segment=get_segment(request), attacklist = get_list())
                attackServer_FileWeb['serverport'] = str(port)
            except Exception as e:
                print(e)

        p = Process(target=httpserver_open,args=(attackServer_FileWeb['serverport'], ))
        #开启子进程，开启服务
        p.start()
        attackServer_FileWeb['serverprocess'] = p.pid
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_FileWeb["id"]).update(attackServer_FileWeb)
        db.session.commit()

    #关闭端口服务               
    if(action == "close" and request.method == "GET"):
        if(attackServer_FileWeb['serverport'] == '0' or attackServer_FileWeb['serverport'] == None):
            print("端口已关闭") 
            return render_template('plugins/FileWeb.html',form=dic, segment=get_segment(request), attacklist = get_list())

        httpserver_close()
        attackServer_FileWeb["serverprocess"] = "NONE"
        attackServer_FileWeb["serverport"] = "0"
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_FileWeb["id"]).update(attackServer_FileWeb)
        db.session.commit()

    #上传文件
    if( request.method == "POST"):
        filedec = request.form.to_dict()['filedec']
        print(filedec)
        f = request.files['webfile']
        upload_path = os.path.join(FILEPATH, f.filename)  #注意：没有的文件夹一定要先创建，不然会提示没有该路径
        f.save(upload_path)

        webfile = WebFile(
            filename= f.filename,
            filepath= FILEPATH,
            adduser = str(current_user),
            dec=filedec
        )
        db.session.add(webfile)
        db.session.commit()

        return redirect("/AttackServer?id={}".format(attackServer_FileWeb['id']))

    #删除文件
    if (request.method == "GET" and action == "delete"):
        fileid = request.args.get("fileid")
        print("fileid!!:" + fileid)
        filename = db.session.query(WebFile).filter(WebFile.id == fileid).first().filename
        db.session.query(WebFile).filter(WebFile.id == fileid).delete()
        db.session.commit()
        try:
            os.chdir(FILEPATH)
            subprocess.Popen(["rm", "-rf", filename])
        except:
            pass
        return redirect("/AttackServer?id={}".format(attackServer_FileWeb['id']))


    webFile = db.session.query(WebFile).all()
    if(webFile == []):
        webFile = {}
    else:
        webFile = queryToDict(webFile)

    #更新数据
    dic = {
        "attackServer_FileWeb" : attackServer_FileWeb,
        "WebFile": webFile,
        "now_ip" : now_ip
    }
    #初始化菜单栏    
    return render_template('plugins/FileWeb.html', form=dic,segment=get_segment(request), attacklist = get_list())

#打开http服务
def httpserver_open(port):
    os.chdir(FILEPATH)
    cmd = 'nohup python3 -m http.server {} &'.format(str(int(port)))
    cmd2 = 'rm -rf nohup.out'
    try:
        os.system(cmd)
        os.system(cmd2)
        
    except Exception as e:
        print(e)
    return 

#关闭http服务
def httpserver_close():
    os.system("ps -ef |grep http.server |awk '{print $2}'|xargs kill -9")
    return