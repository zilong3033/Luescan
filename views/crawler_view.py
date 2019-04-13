#encoding:utf-8
from flask import request,url_for,redirect,render_template,session,jsonify
from . import crawler
from . import mongo
from . import file_path
from lib.check_login import checklogin
from lib.verify_CSRF import verifycsrf
from lib.jinjia_config import env
from lib.crawler_engine import clear_source,run_crawlerscan
import requests,json,copy,os,inspect,threading
from werkzeug.utils import secure_filename
from datetime import datetime


#更新payloads
@crawler.route("/pldupdate")
def payloads_update():
    update_url="http://zilong3033.cn/luescan/getpayloads.json"
    try:
        res=requests.get(update_url)
    except:
        return "连接服务器失败！"
    if res:
        print type(res.content)
        payloads_data=json.loads(res.content)
        print payloads_data["sqli"]
        if payloads_data["sqli"].get("errorbase"):
            mongo.db.sqli.update_one({"type":"errorbase"},{"$set":{"payload":payloads_data["sqli"]["errorbase"]}})
        if payloads_data["sqli"].get("stackedqueries"):
            mongo.db.sqli.update_one({"type":"stackedqueries"},{"$set":{"payload":payloads_data["sqli"]["stackedqueries"]}})
        if payloads_data["sqli"].get("timebase"):
            mongo.db.sqli.update_one({"type":"timebase"},{"$set":{"payload":payloads_data["sqli"]["timebase"]}})
        if payloads_data["sqli"].get("unionquery"):
            mongo.db.sqli.update_one({"type":"unionquery"},{"$set":{"payload":payloads_data["sqli"]["unionquery"]}})
        if payloads_data["sqli"].get("booleanbase"):
            mongo.db.sqli.update_one({"type":"booleanbase"},{"$set":{"payload":payloads_data["sqli"]["booleanbase"]}})
        if payloads_data["xss"]:
            mongo.db.xss.update_one({"type":"reflex_payload"},{"$set":{"payload":payloads_data["xss"]["reflex_payload"]}})
        if payloads_data["server_fingerprint"].get("server_type"):
            mongo.db.server_fp.update_one({"type":"server_type"},{"$set":{"feature":payloads_data["server_fingerprint"].get("server_type")}})
        if payloads_data["server_fingerprint"].get("server_lang"):
            mongo.db.server_fp.update_one({"type":"server_lang"},{"$set":{"feature":payloads_data["server_fingerprint"].get("server_lang")}})
        if payloads_data["server_fingerprint"].get("cookie_type"):
            mongo.db.server_fp.update_one({"type":"cookie_type"},{"$set":{"feature":payloads_data["server_fingerprint"].get("cookie_type")}})
        if payloads_data["server_fingerprint"].get("http_method_danger"):
            mongo.db.server_fp.update_one({"type":"http_method_danger"},{"$set":{"feature":payloads_data["server_fingerprint"].get("http_method_danger")}})
        if payloads_data["server_fingerprint"].get("error_page"):
            mongo.db.server_fp.update_one({"type":"error_page"},{"$set":{"feature":payloads_data["server_fingerprint"].get("error_page")}})
        return "更新成功！"
    return "服务器获取数据异常！"


#爬虫扫描
@crawler.route("/crawlscan")
def crawlscan():
    tasks_dct={}
    ps_id_list=[]
    key=0
    ps_list=mongo.db.clr_ps.find({})
    tasks = mongo.db.clrtasks.find({}).sort("add_time", -1)
    if ps_list:
        for p in ps_list:
            ps_id_list.append(p["clr_id"])
        for task in tasks:
            if task["tasksid"] in ps_id_list:
                tasks_dct[key]=task
                key+=1
                print task
    return render_template("crawlscan.html",tasks_run=tasks_dct)


#运行爬虫引擎
@crawler.route("/clraddtasks",methods=["post"])
def clraddtasks():
    tasksname=request.form.get("tasksname")
    source=request.form.get("source")
    if tasksname and source:
        tasksid=mongo.db.info.find_one({"info":"info"})["tasks_num"]
        tasksid=tasksid+1
        mongo.db.info.update_one({"info": "info"}, {'$set': {'tasks_num': tasksid}})
        add_time=datetime.now()
        urls=clear_source(source)
        tasks={"tasksid":tasksid,"tasksname":tasksname,"urls":urls,"add_time":add_time}
        mongo.db.clrtasks.insert(tasks)
        threading.Thread(target=run_crawlerscan,args=(urls,tasksid)).start()
        return "ok"
    return "error"


#分页显示已完成任务列表
@crawler.route("/clrtaskslist/<int:p_pageid>")
def clrtaskslist(p_pageid):
    tasks_dct={}
    ps_id_list=[]
    key=0
    page_num=4
    n_pageid=p_pageid+1
    ps=mongo.db.clr_ps.find({})
    if ps:
        ps_id_list=[i["clr_id"] for i in ps]
        print ps_id_list
    tasksnum=mongo.db.clrtasks.find({}).count()
    page_tasks=mongo.db.clrtasks.find({"tasksid":{"$ne":ps_id_list}}).sort("add_time", -1).limit(page_num).skip(page_num*p_pageid)
    if tasksnum<=page_num*n_pageid:
        n_pageid="#"
    for i in page_tasks:
        is_run=mongo.db.clr_ps.find_one({"clr_id":i["tasksid"]})
        p_run=1
        if is_run:
            p_run=is_run["p_run"]
        tasks_dct[key]={"tasksid":i["tasksid"],"tasksname":i["tasksname"],"add_time":i["add_time"].strftime("%m-%d %H:%M"), \
                            "urls":i["urls"],"p_run":p_run}
        key+=1
    show_dct={"page_tasks":tasks_dct,"n_pageid":n_pageid}
    return jsonify(show_dct)


#任务删除
@crawler.route("/delclrtask/<int:tasksid>")
def delclrtask(tasksid):
    mongo.db.clrtasks.remove({"tasksid":tasksid})
    mongo.db.clr_ps.remove({"clr_id": tasksid})
    return "已删除"+str(tasksid)+"号任务!"


#任务重扫
@crawler.route("/rerunctask/<int:tasksid>")
def rerunctaks(tasksid):
    if tasksid:
        is_run=mongo.db.clr_ps.find_one({"clr_id":tasksid})
        if not is_run:
            task=mongo.db.clrtasks.find_one({"tasksid":tasksid})
            if task:
                urls=task["urls"]
                threading.Thread(target=run_crawlerscan,args=(urls,tasksid)).start()
                return "重新开始"+str(tasksid)+"号任务！"
            else:
                return "error"
        else:
            return str(tasksid)+"号任务正在运行中!"
    else:
        return "error"

#拉去进度条和扫描信息
@crawler.route("/getps/<int:tasksid>")
def getps(tasksid):
    ps_dict={}
    ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
    if ps:
        ps_dict={"clr_id":ps["clr_id"],"p":str(ps["p"])+"%","p_run":ps["p_run"],"show_mgs":ps["show_mgs"]}
        return jsonify(ps_dict)
    else:
        return "finish"


#中止正在进行的任务
@crawler.route("/stopclrtask/<int:tasksid>")
def stopclrtask(tasksid):
    if tasksid:
        results_id=-1
        ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
        if ps:
            results_id=ps["results_id"]
        mongo.db.cache.remove({"tasksid":tasksid})
        mongo.db.clr_ps.remove({"clr_id":tasksid})
        #数据库回滚
        if results_id!=-1:
            mongo.db.clrresults.remove({"results_id":results_id})
            mongo.db.clrresults_log.remove({"results_id":results_id})
        return "已中止"+str(tasksid)+"号任务!"
    else:
        return "error"

#列出扫描结果
@crawler.route("/cresultlist/<int:tasksid>")
def cresultlist(tasksid):
    cresults_dct={}
    cresult_l_dct={}
    if tasksid:
        cresult_l=mongo.db.clrresults_log.find({"tasksid":tasksid}).sort("start_time",-1)
        cresults=mongo.db.clrresults.find({"tasksid":tasksid})
        tasks=mongo.db.clrtasks.find_one({"tasksid":tasksid})
        key=0
        for i in cresult_l:
            cresult_l_dct[key]=i
            key+=1
        key=0
        for i in cresults:
            cresults_dct[key]=i
            key+=1
        print cresults_dct
        print cresult_l_dct

        #优化1，如果任务正在进行，禁止显示结果
        ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
        return render_template("cresultlist.html",cresults=cresults_dct,cresult_l=cresult_l_dct,tasks=tasks,ps=ps)
    else:
        return "error"

@crawler.route("/delcresult/<int:results_id>")
def delcresults(results_id):
    if results_id:
        mongo.db.clrresults_log.remove({"results_id":results_id})
        mongo.db.clrresults.remove({"results_id":results_id})
        return "已删除"+str(results_id)+"号结果!"
    else:
        return "error"