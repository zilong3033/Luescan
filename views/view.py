#encoding:utf-8
from flask import request,url_for,redirect,render_template,session,jsonify
from . import app
from . import mongo
from . import file_path
from lib.check_login import checklogin
from lib.verify_CSRF import verifycsrf
from lib.jinjia_config import env
from lib.crawler_engine import clear_source,run_crawlerscan
import requests,json,copy,os,inspect,threading
from werkzeug.utils import secure_filename
from datetime import datetime

@app.route("/404")
def NotFound():
    return render_template("404.html")

@app.route('/500')
def Error():
    return render_template('500.html')


#登录页面
@app.route('/login',methods=["get","post"])
def Login():
    if request.method=='GET':
        return render_template("login.html")
    else:
        username=request.form.get("username")
        password=request.form.get("password")
        print username,password
        if username==app.config["loginuser"] and password==app.config["loginpwd"]:
            session["login"]="login_success"
            return "index"
        else:
            return redirect(url_for("Login"))


#首页
@app.route("/")
def Index():
    update_time=""
    official_plugins_num=mongo.db.plugins.find({"source.official":1}).count()
    custom_plugins_num=mongo.db.plugins.find({"source.official":0}).count()
    new_data=mongo.db.plugins.find({}).sort("add_time",-1).limit(1)
    p_tasks_num=mongo.db.pgstasks.find({}).count()
    c_tasks_num=mongo.db.clrtasks.find({}).count()
    tasks_num=p_tasks_num+c_tasks_num
    p_tasks_now_num=mongo.db.pgs_ps.find({}).count()-1  #数据库留了一个样本，把它删掉。。。
    c_tasks_now_num=mongo.db.clr_ps.find({}).count()
    tasks_now_num=p_tasks_now_num+c_tasks_now_num
    for i in new_data:
        if i.has_key("add_time"):
            update_time=i["add_time"]
    update_time=update_time.strftime("%m-%d")

    #近期任务展示
    l_tasks=mongo.db.pgstasks.find({}).sort("add_time",-1).limit(6)
    c_tasks=mongo.db.clrtasks.find({}).sort("add_time",-1).limit(6)
    return render_template("index.html",opn=official_plugins_num,cpn=custom_plugins_num,update_time=update_time,tn=tasks_num,trn=tasks_now_num,l_tasks=l_tasks,c_tasks=c_tasks)


#统计扫描结果,以便绘制饼状图
@app.route("/panalysis")
def analysis():
    #统计某个插件下的感染的主机数
    pluginvulnum={}
    results=mongo.db.pgsresults.find({})
    for result in results:
        for vuls in result["results"]:
            vm=0
            for vul in result["results"][vuls]:
                vm+=1
            if pluginvulnum.has_key(vuls):
                pluginvulnum[vuls]+=vm
            else:
                pluginvulnum[vuls]=vm
    print pluginvulnum
    #统计类型漏洞的感染主机数
    t_num={}
    types=""
    for name in pluginvulnum:
        pdct=mongo.db.plugins.find_one({"name":name})
        if pdct:
            types=pdct["type"]
        if t_num.has_key(types):
            t_num[types]+=pluginvulnum[name]
        else:
            t_num[types]=pluginvulnum[name]
    print t_num

    #爬虫漏洞类型数量统计
    c_results=mongo.db.clrresults.find({})
    for i in c_results:
        if t_num.has_key(i["vul"]):
            t_num[i["vul"]]+=1
        else:
            t_num[i["vul"]]=1
    print t_num
    #统计感染主机数最多的5种类型漏洞
    if len(t_num)>5:
        tup=sorted(t_num.items(),lambda x,y:cmp(x[1],y[1]),reverse = True)[0:5]
        t_num={}
        for i in tup:
            t_num[i[0]]=i[1]
        print t_num
    return render_template("pie.html",t_num=t_num)


@app.route("/logout")
def Logout():
    session["login"]=""
    return redirect(url_for("Login"))


