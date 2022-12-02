# -*- encoding: utf-8 -*-
from hashlib import md5
from flask import render_template, request, flash
from apps import db
import random
import os
import subprocess
from multiprocessing import Process, Manager
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.config import Config


from apps.plugins.models import AttackServer
from apps.utils import get_segment,queryToDict,get_list,get_now_ip,CheckPortSuccess


MODLE_NAME = "FrpServer"
FILEPATH = os.path.dirname(__file__) + "/../../../" + "tools/FrpServer/"
CHINANAME = "FrpServer模块"
FRPCLIENTDIR = "554cca640aff8396632bdb87fb36929c"

#FRP模块
def run():
    # 这里写逻辑
    action = request.args.get('action')
    port = request.args.get('port')

    query = AttackServer.query.filter(AttackServer.model == "FrpServer").first()
    attackServer_frp = queryToDict(query)
    now_ip = get_now_ip(attackServer_frp['id'])
    attackServer_frp['serverhost'] = now_ip

    frpToken = ""
    frpUsername = ""
    frpPassword = ""
    filename = ""
    generateFlag = False

    query = AttackServer.query.filter(AttackServer.model == "FileWeb").first()
    httpport = queryToDict(query)
    httpport = httpport['serverport']
    
    if(attackServer_frp['serverprocess'] != "NONE"):
        frpToken = attackServer_frp['serverprocess'].split(",")[0]
        frpUsername = attackServer_frp['serverprocess'].split(",")[1]
        frpPassword = attackServer_frp['serverprocess'].split(",")[2]
    
    #打开服务
    if(action == "open" and request.method == "GET"):
        #已经开放，不重复开放
        if(attackServer_frp['serverport'] != '0' and attackServer_frp['serverport'] != None):
            print("端口已开放")
            return render_template('plugins/Frp.html',form={"attackServer_frp": attackServer_frp, "now_ip":now_ip,}, segment=get_segment(request), attacklist = get_list())

        #开放在随机端口
        if(port == None or port == "" or port == 0):
            #随机端口
            port = random.randint(30000,31000)
            if(CheckPortSuccess(port)):
                attackServer_frp['serverport'] = str(port) + "," + str(port+50)
            else:
                print("端口冲突请重试")
                flash("端口冲突请重试")
                return render_template('plugins/Frp.html',form={"attackServer_frp": attackServer_frp, "now_ip":now_ip,}, segment=get_segment(request), attacklist = get_list())

        else:
            try:
                if(CheckPortSuccess(port)):
                    attackServer_frp['serverport'] = str(port) + "," + str(int(port)+50)
                else:
                    print("端口冲突请重试")
                    flash("端口冲突请重试")
                    return render_template('plugins/Frp.html',form={"attackServer_frp": attackServer_frp, "now_ip":now_ip,}, segment=get_segment(request), attacklist = get_list())

            except Exception as e:
                print(e)

        controllerport =  attackServer_frp['serverport'].split(",")[1]
        serverport = attackServer_frp['serverport'].split(",")[0]

        frpToken,frpUsername,frpPassword =randomconfig()
        attackServer_frp['serverprocess'] = frpToken + "," + frpUsername + "," + frpPassword

        p = Process(target=Frp_open,args=(controllerport, serverport, frpToken, frpUsername, frpPassword))
        #开启子进程，开启服务
        p.start()
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_frp["id"]).update(attackServer_frp)
        db.session.commit()

    #关闭服务
    if(action == "close" and request.method == "GET"):
        if(attackServer_frp['serverport'] == '0' or attackServer_frp['serverport'] == None):
            print("端口已关闭") 
            return render_template('plugins/Frp.html',form={"attackServer_frp": attackServer_frp, "now_ip":now_ip,}, segment=get_segment(request), attacklist = get_list())

        Frp_close()
        attackServer_frp["serverprocess"] = "NONE"
        attackServer_frp["serverport"] = "0"
        frpToken = ""
        frpUsername = ""
        frpPassword = ""
        controllerport = ""
        serverport = ""
        db.session.query(AttackServer).filter(AttackServer.id == attackServer_frp["id"]).update(attackServer_frp)
        db.session.commit()

    #传入frpc.ini配置生成参数
    if(action == "generate" and request.method == "GET"):
        clientname = request.args.get('clientname') if request.args.get('clientname') != "" else randomCN()
        clientport = request.args.get('clientport') if request.args.get('clientport') != "" else randomCP()
        generateFlag = True

        try:
            controllerport =  attackServer_frp['serverport'].split(",")[1]
            filename = generateini(clientname, clientport)
        except:
            flash("请先打开服务")
            return render_template('plugins/Frp.html',form={"attackServer_frp": attackServer_frp, "now_ip":now_ip,}, segment=get_segment(request), attacklist = get_list())

    else:
        clientname = randomCN()
        clientport = randomCP()

    try:
    #展示服务
        controllerport =  attackServer_frp['serverport'].split(",")[1]
        serverport = attackServer_frp['serverport'].split(",")[0]
        dic = {
            "now_ip":now_ip,
            "frpToken": frpToken,
            "frpUsername": frpUsername,
            "frpPassword": frpPassword,
            "controllerport": controllerport,
            "serverport":serverport,
            "attackServer_frp":attackServer_frp,
            "httpport":httpport,
            "clientname": clientname,
            "clientport": clientport,
            "generateFlag": generateFlag,
            "filename":filename
        }
    except:
        dic = {
        "now_ip":now_ip,
        "frpToken": frpToken,
        "frpUsername": frpUsername,
        "frpPassword": frpPassword,
        "controllerport": "",
        "serverport":"",
        "attackServer_frp":attackServer_frp,
        "httpport":httpport,
        "clientname": clientname,
        "clientport": clientport,
        "generateFlag": generateFlag,
        "filename":filename
    }
    #初始化菜单栏
    return render_template('plugins/Frp.html', form=dic, segment=get_segment(request), attacklist = get_list())



#打开frp服务
def Frp_open(controllerport, serverport, frpToken, frpUsername, frpPassword):

    os.chdir(FILEPATH)
    print(FILEPATH)
    shutil.copy(FILEPATH + 'config_tmp.ini', FILEPATH + 'config.ini')

    # 正式用这个
    cmd = '''sed -i 's/controllerport/{}/g' config.ini &&
    sed -i 's/serverport/{}/g' config.ini &&
    sed -i 's/frpToken/{}/g' config.ini &&
    sed -i 's/frpUsername/{}/g' config.ini &&
    sed -i 's/frpPassword/{}/g' config.ini
    '''.format(str(controllerport),str(serverport),str(frpToken),str(frpUsername),str(frpPassword))

    # mac写代码用这个
    # cmd = '''gsed -i 's/controllerport/{}/g' config.ini &&
    # gsed -i 's/serverport/{}/g' config.ini &&
    # gsed -i 's/frpToken/{}/g' config.ini &&
    # gsed -i 's/frpUsername/{}/g' config.ini &&
    # gsed -i 's/frpPassword/{}/g' config.ini
    # '''.format(str(controllerport),str(serverport),str(frpToken),str(frpUsername),str(frpPassword))


    cmd2 = 'nohup ./frps_linux -c config.ini &'
    try:
        os.system(cmd)
        os.system(cmd2)
    except Exception as e:
        print(e)
    return 

#关闭frp服务
def Frp_close():
    os.system("ps -ef |grep frps |awk '{print $2}'|xargs kill -9")
    return

def randomconfig():
    token = random.randint(0,10000000000)
    token = md5(str(token).encode(encoding='UTF-8')).hexdigest()
    username = random.randint(20000000000,30000000000)
    username = md5(str(username).encode(encoding='UTF-8')).hexdigest()
    password = random.randint(30000000000,40000000000)
    password = md5(str(password).encode(encoding='UTF-8')).hexdigest()

    return token, username, password

def randomCN():
    clientname = random.randint(0,10000000000)
    clientname = md5(str(clientname).encode(encoding='UTF-8')).hexdigest()[:6]
    return clientname

def randomCP():
    clientport = random.randint(40000,45000)
    return str(clientport)

def generateini(clientname, clientport):
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    query = session.query(AttackServer).filter(AttackServer.model == "FrpServer").first()
    attackServer = queryToDict(query)
    serverip = attackServer['serverhost']
    serverport = attackServer['serverport'].split(",")[0]
    frpToken = attackServer['serverprocess'].split(",")[0]

    filename = md5(str(clientname + clientport).encode(encoding='UTF-8')).hexdigest()[:8]
    print(filename)    
    shutil.copy(FILEPATH + 'frpc_config_tmp.ini', FILEPATH + '../FileWeb/554cca64/' + filename)
    os.chdir(FILEPATH + '../FileWeb/554cca64/')
    # mac写代码用这个
    # cmd = "gsed -i 's/serverip/{}/g' {} &&".format(str(serverip), filename)
    # cmd = cmd + "gsed -i 's/serverport/{}/g' {} &&".format(str(serverport), filename)
    # cmd = cmd + "gsed -i 's/clientname/{}/g' {} &&".format(str(clientname), filename)
    # cmd = cmd + " gsed -i 's/remoteport/{}/g' {} &&".format(str(clientport), filename)
    # cmd = cmd + " gsed -i 's/frpToken/{}/g' {}".format(str(frpToken), filename)

    # 正式写代码用这个
    cmd = "sed -i 's/serverip/{}/g' {} &&".format(str(serverip), filename)
    cmd = cmd + "sed -i 's/serverport/{}/g' {} &&".format(str(serverport), filename)
    cmd = cmd + "sed -i 's/clientname/{}/g' {} &&".format(str(clientname), filename)
    cmd = cmd + " sed -i 's/remoteport/{}/g' {} &&".format(str(clientport), filename)
    cmd = cmd + " sed -i 's/frpToken/{}/g' {}".format(str(frpToken), filename)

    try:
        os.system(cmd)
    except Exception as e:
        print(e)

    

    return filename