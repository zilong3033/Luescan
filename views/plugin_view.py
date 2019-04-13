#encoding:utf-8
from flask import request,url_for,redirect,render_template,session,jsonify
from . import plugin
from . import mongo
from . import file_path
from lib.check_login import checklogin
from lib.verify_CSRF import verifycsrf
from lib.jinjia_config import env
from lib.plugin_engine import translate_source_urls, translate_source_hosts,run_tasks,bp_run_task,tasks_global
import requests,json,copy,os,inspect,threading
from werkzeug.utils import secure_filename
from datetime import datetime

#插件扫描页面
@plugin.route("/pluginscan")
def pluginscan():
    plugins_list = mongo.db.plugins.find({})
    return render_template("pgstasks.html",plugins_list=plugins_list)

#更新下载插件
@plugin.route("/pgsupdate")
def pgsupdate():
    update_url="http://zilong3033.cn/luescan/getplugins.json"
    try:
        rep=requests.get(update_url)
    except:
        return "连接更新服务器失败!"
    plugins_data=json.loads(rep.text)
    if plugins_data:
        need_update=copy.deepcopy(plugins_data)
        local_plugins=mongo.db.plugins.find({"source.official":1})
        for lp in local_plugins:
            for p in plugins_data:
                if plugins_data[p]["name"]==lp["name"] and plugins_data[p]["source"]["changeid"]==0:
                    if need_update.has_key(p):
                        need_update.pop(p)
        download_url="http://zilong3033.cn/luescan/vuldb/"
        for p in need_update:
            #插件信息在数据库
            need_update[p]["add_time"]=datetime.now()
            mongo.db.plugins.insert(need_update[p])
            mongo.db.pgsupdate.insert(need_update[p])
            plugin_filename=str(need_update[p]["filename"]+".py")
            print repr(file_path+plugin_filename)
            if os.path.exists(file_path+plugin_filename):
                os.remove(file_path+plugin_filename)
            download=download_url+plugin_filename
            print download
            rep=requests.get(download)
            f=open(file_path+plugin_filename,"w+")
            f.write(rep.text)
            f.close()
    return "更新已完成!"


#需要更新的插件数
@plugin.route("/upadate_check")
def updatecheck():
    #official_plugins_num = mongo.db.plugins.find({"source.official": 1}).count()
    need_num = 0
    update_url = "http://zilong3033.cn/luescan/getplugins.json"
    try:
        rep = requests.get(update_url)
    except:
        return "连接更新服务器失败!"
    plugins_data = json.loads(rep.text)
    if plugins_data:
        need_update = copy.deepcopy(plugins_data)
        local_plugins = mongo.db.plugins.find({"source.official": 1})
        for lp in local_plugins:
            for p in plugins_data:
                if plugins_data[p]["name"] == lp["name"] and plugins_data[p]["source"]["changeid"] == 0:
                    if need_update.has_key(p):
                        need_update.pop(p)
        need_num=str(len(need_update))
    return need_num


#插件上传
@plugin.route("/plugins_upload",methods=["post"])
def plgupload():
    file_check_one=["name","level","source","type"]
    file_check_two=["official","changeid"]
    f=request.files["file"]
    if f:
        file_name=secure_filename(f.filename)
        print file_name
        if file_name.split(".")[-1]=="py":
            filepath=file_path+file_name
            try:
                check_filename = mongo.db.plugins.find_one({"filename": file_name.split(".")[0]})
                if check_filename:
                    return "插件名重复，请重新命名插件文件名!"
                f.save(filepath)
                module=__import__(file_name.split(".")[0])
                plugin_info=module.plugin_info()
            except:
                os.remove(filepath)
                return "file_upload_fail1"
            #检查插件是否合规:
            if not plugin_info:
                os.remove(filepath)
                return "插件不规范!没有插件信息!"
            if not plugin_info["source"]:
                return "插件不规范!插件缺少source信息"
            for l in file_check_one:
                if l not in plugin_info:
                    os.remove(filepath)
                    return "插件不规范!基本信息不全"
            for l in file_check_two:
                if l not in plugin_info["source"]:
                    os.remove(filepath)
                    return "插件不规范!插件source信息不全"
            check_name=mongo.db.plugins.find_one({"name":plugin_info["name"]})
            if check_name:
                os.remove(filepath)
                return "已有该插件漏洞!"
            plugin_info["filename"]=file_name.split(".")[0]
            plugin_info["add_time"]=datetime.now()
            mongo.db.plugins.insert(plugin_info)
            return "file_upload_succss"
        return "file_upload_fail2"
    return "file_upload_fail3"

#上传页面
@plugin.route("/upload_plugins")
def uploadplugins():
    return render_template("upload_plugins.html")

#添加目标任务数据，列出可用插件信息。
@plugin.route("/addsource",methods=["post"])
def addsource():
    plugins_two={}
    plugins_one={}
    key1=key2=0
    source_type=request.form.get("source_type")
    print source_type
    plugins_list=mongo.db.plugins.find({})
    for p in plugins_list:
        module=__import__(p["filename"])
        args_num=len(inspect.getargspec(module.check).args)
        p.pop(u"filename")
        p.pop(u"add_time")
        p.pop("_id")
        if args_num==2:
            key1+=1
            plugins_two[key1]=p
        if args_num==1:
            key2+=1
            plugins_one[key2]=p
    if "urls" in source_type:
        return jsonify(plugins_one)
    if "hosts" in source_type:
        return jsonify(plugins_two)
    return redirect(url_for("Error"))


#列出可用插件
@plugin.route("/pluginslist")
def pluginslist():
    plugins_list=mongo.db.plugins.find({})
    return render_template("pluginslist.html",plugins_list=plugins_list)


#批量删除插件
@plugin.route("/deleteplugins",methods=["post"])
def deleteplugins():
    delplist=request.form.get("delplist")
    delpdct=json.loads(delplist)
    for p in delpdct:
        print p["name"]
        pdct=mongo.db.plugins.find_one({"name":p["name"]})
        #mongo.db.plugins.remove({"name":p["name"]})
        #os.remove(file_path+pdct["filename"]+".py")
    return "删除插件成功!"


#添加任务
@plugin.route("/addtasks",methods=["post"])
def addtasks():
    pfilelist={}
    tasksname=request.form.get("tasksname")
    source_type = request.form.get("source_type")
    source = request.form.get("source")
    plist=request.form.get("plist")
    plist_dct=json.loads(plist)
    if source_type:
        for i in plist_dct:
            pfilelist[i["name"]]=mongo.db.plugins.find_one({"name":i["name"]})["filename"]
        #新建的任务写入数据库
        # info集合里存储已经添加的任务数信息。
        tasksid=mongo.db.info.find_one({})["tasks_num"]
        print tasksid
        tasksid=tasksid+1
        mongo.db.info.update_one({"info": "info"}, {'$set': {'tasks_num': tasksid}})
        if "urls" in source_type:
            urls_dct = translate_source_urls(source)
            tasks = {"tasksname": tasksname, "tasksid": tasksid, "add_time": datetime.now(), "urls": urls_dct,
                     "plugins": pfilelist}
            mongo.db.pgstasks.insert(tasks)
            threading.Thread(target=run_tasks, args=(urls_dct, pfilelist, tasksid)).start()
        if "hosts" in source_type:
            hosts_dct = translate_source_hosts(source)
            print hosts_dct
            tasks = {"tasksname": tasksname, "tasksid": tasksid, "add_time": datetime.now(), "hosts": hosts_dct,
                     "plugins": pfilelist}
            mongo.db.pgstasks.insert(tasks)
            mongo.db.info.update_one({"info":"info"},{'$set':{'tasks_num':tasksid}})
            threading.Thread(target=run_tasks, args=(hosts_dct, pfilelist, tasksid)).start()
        #运行任务
        #run_tasks(urls_dct,pfilelist,tasksid)
    return "a"


#列出某任务所有扫描结果
@plugin.route("/presultlist/<int:tasksid>")
def pgstaskslist(tasksid):
    tasks=mongo.db.pgstasks.find_one({"tasksid":tasksid})
    results=mongo.db.pgsresults.find({"taskid":tasksid}).sort("start_time",-1)
    return render_template("presultlist.html",tasks=tasks,results=results)


#删除某任务
@plugin.route("/delpgstasks/<int:tasksid>")
def delpgstasks(tasksid):
    print tasksid
    mongo.db.pgstasks.remove({"tasksid":tasksid})
    mongo.db.pgsresults.remove({"taskid":tasksid})
    return "删除"+str(tasksid)+"号任务成功！"


#重新运行任务
@plugin.route("/rerunptasks/<int:tasksid>")
def reruntasks(tasksid):
    ps=mongo.db.pgs_ps.find_one({"ps_id":tasksid})
    if ps:             #断点继续扫描
        if ps["p_run"]==1:
            bp=mongo.db.pgsbpoint.find_one({})
            if bp:
                results=bp["results"]
                bpdata=bp["bpdata"]
                source_type=bp["source_type"]
                task_num=bp["task_num"]
                threading.Thread(target=bp_run_task,args=(tasksid,bpdata,results,source_type,task_num)).start()
                with plugin.plugin_context():
                    mongo.db.pgsbpoint.remove({"tasksid": tasksid})
            return "继续"+str(tasksid)+"号扫描!"
        else:
            return "任务正在运行!"
    else:
        ptasks=mongo.db.pgstasks.find_one({"tasksid":tasksid})
        print ptasks
        if ptasks.has_key("urls"):
            urls_dct=ptasks["urls"]
            pfilelist = ptasks["plugins"]
            threading.Thread(target=run_tasks, args=(urls_dct, pfilelist, tasksid)).start()
        if ptasks.has_key("hosts"):
            hosts_dct=ptasks["hosts"]
            pfilelist=ptasks["plugins"]
            threading.Thread(target=run_tasks,args=(hosts_dct,pfilelist,tasksid)).start()
        #run_tasks(urls,pfilelist,tasksid)
        return redirect(url_for("pluginscan"))


#删除某任务的所有扫描结果
@plugin.route("/delpresult/<int:tasksid>")
def delpresult(tasksid):
    print tasksid
    mongo.db.pgsresults.remove({"taskid":tasksid})
    return "已删除"+str(tasksid)+"号扫描结果!"


#暂停任务
@plugin.route("/stopptasks/<int:tasksid>")
def stopptasks(tasksid):
    ps=mongo.db.pgs_ps.find_one({"ps_id":tasksid})
    signstop=1
    if ps:
        mongo.db.pgs_ps.update_one({"ps_id": tasksid}, {'$set': {"p_run":1}})
        return str(signstop)
    else:
        signstop=0
        return str(signstop)


#读取正在进行的任务
@plugin.route("/pntask")
def pgsps():
    tasks_dct = {}
    signfinish=0
    key=0
    tasks = mongo.db.pgstasks.find({}).sort("add_time", -1)
    ps_list=mongo.db.pgs_ps.find({})
    ps_id_list = [p["ps_id"] for p in ps_list]
    for i in tasks:
        if i["tasksid"] in ps_id_list:
            ps = mongo.db.pgs_ps.find_one({"ps_id": i["tasksid"]})
            key+=1
            if tasks_global.get(i["tasksid"])=="task_finish":
                signfinish=1
                tasks_global.pop(i["tasksid"],None)
                print tasks_global
                mongo.db.pgs_ps.remove({"ps_id":i["tasksid"]})
            if i.has_key("urls"):
                tasks_dct[key]={"tasksname":i["tasksname"],"add_time":i["add_time"].strftime("%m-%d %H:%M"),"tasksid":i["tasksid"],"urls":i["urls"],"plugins":i["plugins"],"ps":ps["p"],"is_stop":ps["p_run"],"is_finish":signfinish}
            else:
                tasks_dct[key] = {"tasksname": i["tasksname"], "add_time": i["add_time"].strftime("%m-%d %H:%M"),
                                  "tasksid": i["tasksid"], "hosts": i["hosts"], "plugins": i["plugins"], "ps": ps["p"],"is_stop":ps["p_run"],"is_finish":signfinish}
    return jsonify(tasks_dct)


#中止正在运行的任务
@plugin.route("/killtasks/<int:tasksid>")
def killtasks(tasksid):
    mongo.db.pgs_ps.remove({"ps_id": tasksid})
    #mongo.db.pgstasks.remove({"tasksid":tasksid})
    return "已中止"+str(tasksid)+"号任务!"


#列出所有任务。
@plugin.route("/ptasklist/")
def ptasklist():
    tasks_dct={}
    key=0
    tasks = mongo.db.pgstasks.find({}).sort("add_time", -1)
    ps_list=mongo.db.pgs_ps.find({})
    ps_id_list=[p["ps_id"] for p in ps_list]
    for i in tasks:
        if i["tasksid"] not in ps_id_list:
            key+=1
            if i.has_key("urls"):
                tasks_dct[key]={"tasksname":i["tasksname"],"add_time":i["add_time"].strftime("%m-%d %H:%M"),"tasksid":i["tasksid"],"urls":i["urls"],"plugins":i["plugins"]}
            else:
                tasks_dct[key] = {"tasksname": i["tasksname"], "add_time": i["add_time"].strftime("%m-%d %H:%M"),
                                  "tasksid": i["tasksid"], "hosts": i["hosts"], "plugins": i["plugins"]}
    return jsonify(tasks_dct)