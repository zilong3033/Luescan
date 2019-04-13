#encoding:utf-8
from .. import file_path,mongo,app
from datetime import datetime
import base64,time
from Queue import Queue

tasks_global={}

#解析source数据,以便存储和运行任务
def translate_source_urls(urls):
    urls_dct={}
    lst=urls.strip(" ").replace("\n","").split(";")
    if "" in lst:
        lst.remove("")
    urls_dct["urls"]=list(set(lst))
    return urls_dct

def translate_source_hosts(hosts):
    hosts_dct={}
    host=[]
    hplst=[]
    hst=hosts.strip(" ").replace("\n","").split(";")
    if "" in hst:
        hst.remove("")
    for i in hst:
        hplst=i.split(":")
        host.append(hplst)
    host_=[]
    for i in host:
        if i not in host_:
            host_.append(i)
    hosts_dct["hosts"]=host_
    return hosts_dct

#开始资源分配到队列
def run_tasks(source_dct,pfilelist,taskid):
    q=Queue()
    source_type=""
    results={}
    print source_dct
    print pfilelist
    if source_dct.has_key("urls"):
        source_type="urls"
    if source_dct.has_key("hosts"):
        source_type="hosts"
    for plugin in pfilelist:
        for source in source_dct[source_type]:
            task=(plugin,source,pfilelist[plugin])
            q.put(task)
    task_num=q.qsize()
    with app.app_context():
        mongo.db.pgs_ps.insert({"ps_id":taskid,"p_run":0,"p":"0%"})
    run_task(q,taskid,source_type,results,task_num)


#断点续扫引擎
def bp_run_task(tasksid,bpdata,results,source_type,task_num):
    q=Queue()
    with app.app_context():
        mongo.db.pgs_ps.update_one({"ps_id": tasksid}, {'$set': {"p_run": 0}})
    for b in bpdata:
            task=(b[0],b[1],b[2])
            q.put(task)
    run_task(q,tasksid,source_type,results,task_num)


#运行插件单元引擎
def run_task(q,taskid,source_type,results,task_num):
    task=()
    p_result=[]
    percent=0.0
    signkill=0      #终止正在运行的任务的消息,将清空资源池和任务列表池
    signstop=0      #暂停任务,并保存任务资源到pgsbpoint集合中
    stop_data=[]    #暂停时，保留未运行的资源。
    #统计单任务数:
    finish=0
    start_time=datetime.now()
    while not q.empty():
        task=q.get()
        print task
        if len(task)==3:
            module=__import__(task[2])
            if source_type=="urls":
                result=module.check(task[1])
            if source_type=="hosts":
                result = module.check(task[1][0],task[1][1])
            finish=task_num-q.qsize()
            percent=float(finish)/float(task_num)
            time.sleep(3)
            print "任务已完成:" + str(int(percent * 100)) + "%"

            with app.app_context():    #每运行一个单元，从ps里获取终止信号。
                is_ps=mongo.db.pgs_ps.find_one({"ps_id":taskid})
                if not is_ps:
                    while not q.empty():  #释放资源
                        q.get()
                    signkill=1
                else:
                    mongo.db.pgs_ps.update_one({"ps_id": taskid}, {'$set': {"p": str(int(percent*100))+"%"}})

            if result:
                if source_type=="hosts":
                    url=(":").join(task[1])
                else:
                    url=task[1]
                url=base64.b64encode(url)
                p_result.append((task[0],url,result))
                result = ""

            with app.app_context():     #暂停任务，从ps里获取暂停信号
                ps=mongo.db.pgs_ps.find_one({"ps_id":taskid})
                if ps:
                    is_stop=ps["p_run"]
                    if is_stop==1:
                        while not q.empty():
                            task=q.get()
                            stop_data.append(task)
                        signstop=1
    #整理扫描结果以便存储
    for i in p_result:
        if not results.has_key(i[0]):
            results[i[0]]={}
    for i in p_result:
        results[i[0]][i[1]]=i[2]
    print results
    print stop_data
    result_data={"taskid":taskid,"start_time":start_time,"results":results}

    reserve={"tasksid":taskid,"stop_time":start_time,"results":results,"bpdata":stop_data,"source_type":source_type,"task_num":task_num}
    with app.app_context():
        print signstop
        if signkill==0 and signstop==0:  #没有终止信号和暂停信号，就将结果存入数据库。
            mongo.db.pgsresults.insert(result_data)
            tasks_global[taskid]="task_finish"
        if signstop==1:
            mongo.db.pgsbpoint.insert(reserve)

#非资源池运行hosts型插件
def run_tasks_hosts(source_dct,pfilelist,taskid):
    print source_dct
    print pfilelist
    url_result={}
    results={}
    task_num_flg=0.0
    task_num=0.0
    percent=0.0
    signkill=0      #暂停正在运行的任务的消息,将清空资源池和任务列表池
    #统计单任务数:
    for plugin in pfilelist:
        for hp in source_dct["hosts"]:
            task_num_flg+=1
    task_num=task_num_flg
    with app.app_context():
        mongo.db.pgs_ps.insert({"ps_id":taskid,"p_run":1,"p":"%0"})
    start_time=datetime.now()
    if source_dct.has_key("hosts"):
        for plugin in pfilelist.keys():
            for hp in source_dct["hosts"]:
                time.sleep(3)
                if pfilelist.has_key(plugin):
                    module = __import__(pfilelist[plugin])
                    result=module.check(hp[0],hp[1])
                    task_num_flg -= 1
                    percent = (task_num - task_num_flg) / task_num
                    print "任务已完成:"+str(int(percent*100))+"%"
                    time.sleep(2)
                with app.app_context():
                    is_ps=mongo.db.pgs_ps.find_one({"ps_id":taskid})
                    if not is_ps:
                        source_dct["hosts"]={}
                        pfilelist={}
                        signkill=1
                    else:
                        mongo.db.pgs_ps.update_one({"ps_id": taskid}, {'$set': {"p": str(int(percent*100))+"%"}})
                if result:
                    hp=":".join(hp)
                    hp=base64.b64encode(hp)
                    url_result[hp]=result
                    results[plugin] = url_result
                    result=""
            url_result={}
        print results
        result={"taskid":taskid,"start_time":start_time,"results":results}
        with app.app_context():
            if signkill==0:
                mongo.db.pgsresults.insert(result)
                mongo.db.pgs_ps.remove({"ps_id":taskid})
