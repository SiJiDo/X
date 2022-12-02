# -*- encoding: utf-8 -*-

from ctypes import util
from statistics import mode
from flask import Blueprint
from importlib import import_module
import os
from apps.plugins.models import AttackServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.config import Config
from apps.utils import queryToDict

blueprint = Blueprint(
    'plugins_blueprint',
    __name__,
    url_prefix=''
)

# 创建DBSession类型:
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
DBSession = sessionmaker(bind=engine)
session = DBSession()

#这里添加组件
try:
    model_list = os.listdir("apps/plugins/Workplace/")
except:
    model_list = []

#数据库中不存在的组件进行删除
if(model_list != []):
    attackServer = session.query(AttackServer).all()
    if (attackServer != []):
        attackServer = queryToDict(attackServer)
        for i in attackServer:
            flag = False
            for j in model_list:
                module_name = j.split('.py')[0]
                module = import_module('apps.plugins.Workplace.{}'.format(module_name))
                if(i['model'] == module_name):
                    flag = True
            if(flag == False):
                session.query(AttackServer).filter(AttackServer.id == i['id']).delete()
                session.commit()

for i in model_list:
    module_name = i.split('.py')[0]
    if("_" in module_name):
        continue
    module = import_module('apps.plugins.Workplace.{}'.format(module_name))
    
    print(module.MODLE_NAME)
    c = session.query(AttackServer).filter(AttackServer.model == module.MODLE_NAME).count()
    #先筛选出存在的组件进行保留
    if c > 0:
        continue

    #不存在的组件进行添加
    else:
        #添加模块
        print("开始添加 --" + module.MODLE_NAME)
        attackServer = AttackServer(
            model = module.MODLE_NAME,
            filepath = module.FILEPATH,
            chinaname= module.CHINANAME,
            serverhost = "0.0.0.0",
            serverport = 0,
            serverprocess = "NONE"
        )

        # #刷新配置，先删再加
        # result = session.query(AttackServer).all()
        # [session.delete(r) for r in result]
        # session.commit()

        session.add(attackServer)
        session.commit()
    
try:
    frpclist = os.listdir("tools/FileWeb/554cca64/")
    for i in frpclist:
        if(len(i) == 8):
            os.remove("tools/FileWeb/554cca64/" + i)
except:
    pass

print("AttackServer 启动成功")

session.close()

    