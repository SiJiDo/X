# -*- coding: utf-8 -*-
from pickle import FALSE
import time
import signal
from subprocess import Popen
import requests

import re
from flask.globals import request
from sqlalchemy.sql.expression import true
from flask import flash
from datetime import datetime as cdatetime #有时候会返回datatime类型
from datetime import date,time
from flask_sqlalchemy import Model
from sqlalchemy import DateTime,Numeric,Date,Time #有时又是DateTime
from flask_login import current_user

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.config import Config
from apps.plugins.models import AttackServer


class SubProcessSrc(object):
    """Running the process in a separate thread
       and outputting the stdout and stderr simultaneously.
       result dict with status and proc. status = 1 means process not completed.
       status = 0 means process completed successfully.
    """
    def __init__(self, cmd, cwd, shell=False, timeout=604800):
        self.cmd = cmd
        self.timeout = timeout
        self.proc = None
        self.shell = shell
        self.revoked = False
        self.cwd = cwd

    def run(self):
        signal.signal(signal.SIGTERM, self.sigterm_hander)
        self.proc = Popen(self.cmd, shell=self.shell, cwd=self.cwd)

        is_timeout = True
        for i in range(self.timeout):
            if self.proc.poll() is not None:
                is_timeout = False
                break
            time.sleep(1)

        result = {'proc': self.proc}

        if self.revoked:
            result['status'] = -1
        elif is_timeout: # Process not completed
            result['status'] = 1
        else:  # Process completed successfully.
            result['status'] = 0

        return result

    def sigterm_hander(self, signum, frame):
        self.proc.terminate()
        self.proc.wait()
        self.revoked = True

#查询结果转字典
def queryToDict(models):
    if(isinstance(models,list)):
        if(isinstance(models[0],Model)):
            lst = []
            for model in models:
                gen = model_to_dict(model)
                dit = dict((g[0],g[1]) for g in gen)
                lst.append(dit)
            return lst
        else:
            res = result_to_dict(models)
            return res
    else:
        if (isinstance(models, Model)):
            gen = model_to_dict(models)
            dit = dict((g[0],g[1]) for g in gen)
            return dit
        else:
            res = dict(zip(models.keys(), models))
            find_datetime(res)
            return res

#当结果为result对象列表时，result有key()方法
def result_to_dict(results):
    res = [dict(zip(r.keys(), r)) for r in results]
    #这里r为一个字典，对象传递直接改变字典属性
    for r in res:
        find_datetime(r)
    return res
    
def model_to_dict(model):      #这段来自于参考资源
    for col in model.__table__.columns:
        if isinstance(col.type, DateTime):
            value = convert_datetime(getattr(model, col.name))
        elif isinstance(col.type, Numeric):
            value = float(getattr(model, col.name))
        else:
            value = getattr(model, col.name)
    #     print(str(col.name) + ":" + str(value))
    #     dic[col.name] = value
    # return dic
        yield (col.name, value)

def model_to_dict_2(model):      #这段来自于参考资源
    dic = {}
    for col in model.__table__.columns:
        if isinstance(col.type, DateTime):
            value = convert_datetime(getattr(model, col.name))
        elif isinstance(col.type, Numeric):
            value = float(getattr(model, col.name))
        else:
            value = getattr(model, col.name)
        dic[col.name] = value
    return dic


def find_datetime(value):
    for v in value:
        if (isinstance(value[v], cdatetime)):
            value[v] = convert_datetime(value[v])   #这里原理类似，修改的字典对象，不用返回即可修改
def convert_datetime(value):
    if value:
        if(isinstance(value,(cdatetime,DateTime))):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif(isinstance(value,(date,Date))):
            return value.strftime("%Y-%m-%d")
        elif(isinstance(value,(Time,time))):
            return value.strftime("%H:%M:%S")
    else:
        return ""

#dict转换为form
def dict_to_form(dict, form):
    form_key_list = [k for k in form.__dict__]
    for k, v in dict.items():
        if k in form_key_list and v:
            field = form.__getitem__(k)
            field.data = v
            form.__setattr__(k, field)

#字段错误提示
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash("字段 [%s] 格式有误,错误原因: %s" % (
                getattr(form, field).label.text,
                error
            ))

## 字符串转字典
def str_to_dict(dict_str):
    if isinstance(dict_str, str) and dict_str != '':
        new_dict = json.loads(dict_str)
    else:
        new_dict = ""
    return new_dict


## URL解码
def urldecode(raw_str):
    return unquote(raw_str)


# HTML解码
def html_unescape(raw_str):
    return html.unescape(raw_str)


# 字典转对象
def dict_to_obj(dict, obj, exclude=None):
    for key in dict:
        if exclude:
            if key in exclude:
                continue
        setattr(obj, key, dict[key])
    return obj


# peewee转dict
def obj_to_dict(obj, exclude=None):
    dict = obj.__dict__['_data']
    if exclude:
        for key in exclude:
            if key in dict: dict.pop(key)
    return dict


# peewee转list
def query_to_list(query, exclude=None):
    list = []
    for obj in query:
        dict = obj_to_dict(obj, exclude)
        list.append(dict)
    return list


def form_to_model(form, model):
    for wtf in form:
        model.__setattr__(wtf,form[wtf])
    return model


# peewee模型转表单
def model_to_form(model, form):
    dict = obj_to_dict(model)
    form_key_list = [k for k in form.__dict__]
    for k, v in dict.items():
        if k in form_key_list and v:
            field = form.__getitem__(k)
            field.data = v
            form.__setattr__(k, field)


def get_segment( request ): 

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  

def get_list():
    # 创建DBSession类型:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    attackserver_query = session.query(AttackServer).all()
    if(attackserver_query == []):
        attackserver_query = {}
    else:
        attackserver_query = queryToDict(attackserver_query)    
    session.close()
    dic = {
        'attackserver': attackserver_query
    }
    return dic

def get_now_ip(id = 0):
    if(id == 0):
        r = requests.get("http://www.cip.cc", headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:104.0) Gecko/20100101 Firefox/104.0"})
        split1 = "IP	: "
        split2 = "\n"
        print(r.text)
        try:
            ip = r.text.split(split1)[1].split(split2)[0]
        except:
            print("ip 获取失败")
        return ip
        
    else:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        DBSession = sessionmaker(bind=engine)
        session = DBSession()

        attackserver_query = session.query(AttackServer).filter(AttackServer.id == id).first()
        attackserver_query = queryToDict(attackserver_query)
        if(attackserver_query['serverhost'] == '0.0.0.0'):
            r = requests.get("http://www.cip.cc", headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:104.0) Gecko/20100101 Firefox/104.0"})
            split1 = "IP	: "
            split2 = "\n"
            print(r.text)
            try:
                attackserver_query['serverhost'] = r.text.split(split1)[1].split(split2)[0]
                session.query(AttackServer).filter(AttackServer.id == id).update(attackserver_query)
                session.commit()
            except:
                print("ip 获取失败")
        session.close()
        return  attackserver_query['serverhost']
        return ip

def CheckPortSuccess(port):
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    l = []
    
    reslut = session.query(AttackServer).all()
    reslut = queryToDict(reslut)
    for i in reslut:
        if("," in i['serverport']):
            l.extend(i['serverport'].split(","))
        else:
            l.append(i['serverport'])
    session.close()
    if(str(port) in l and str(port) != "0"):
        return False
    return True
