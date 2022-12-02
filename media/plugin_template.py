# -*- encoding: utf-8 -*-
from flask import render_template, request
from apps import db
import random
import os
import subprocess
from multiprocessing import Process

from apps.plugins.models import AttackServer
from apps.utils import get_segment,queryToDict,get_list


MODLE_NAME = "xxx"
FILEPATH = "/tmp/cobaltstrack"
CHINANAME = "CS开启管理器"

#xx模块
def run():
    # 这里写逻辑


    #展示服务
    dic = {}
    #初始化菜单栏    
    return render_template('plugins/xxx.html', form=dic, segment=get_segment(request), attacklist = get_list())
