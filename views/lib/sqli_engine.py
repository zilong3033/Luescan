# encoding:utf-8
import requests
import json
import time
import threading
from .. import app,mongo
from datetime import datetime


sqlmap_results = []
results = {}

lock = threading.Lock()


class AutoSql(object):
    taskid = ""
    start_time = 0

    def __init__(self, server, target,tasksid):
        self.server = server
        self.target = target
        self.tasksid=tasksid

    def task_new(self):
        urls = self.server + "/task/new"
        new_data = requests.get(urls)
        dct = new_data.json()
        self.taskid = dct["taskid"]
        if self.taskid:
            return True
        else:
            return False

    def task_delete(self):
        urls = self.server + "/task/" + self.taskid + "/delete"
        data = requests.get(urls)
        dct = data.json()
        if dct["success"]:
            return True
        else:
            return False

    def scan_start(self):
        urls = self.server + "/scan/" + self.taskid + "/start"
        target_json = json.dumps({"url": self.target})
        start_data = requests.post(urls, data=target_json, headers={"Content-Type": "application/json"})
        self.start_time = time.time()
        dct = start_data.json()
        if dct["success"]:
            return True
        else:
            return False

    def scan_status(self):
        urls = self.server + "/scan/" + self.taskid + "/status"
        status_data = requests.get(urls)
        return status_data.json()["status"]

    def scan_data(self):
        data_result = {}
        result = {}
        key = 0
        urls = self.server + "/scan/" + self.taskid + "/data"
        result_data = requests.get(urls)
        dct = result_data.json()
        if not dct["data"]:
            pass
        else:  # these data can jump to json
            print "the bug count is %d" % len(dct["data"][1]["value"][0]["data"])
            for i in dct["data"][1]["value"][0]["data"]:
                key=str(key)
                data_result[key] = {"title": dct["data"][1]["value"][0]["data"][i]["title"],
                                    "payload": dct["data"][1]["value"][0]["data"][i]["payload"]}
                key=int(key)+1
            result["data"] = data_result
            result["dbms"] = dct["data"][1]["value"][0]["dbms"]
            result["dbms_version"] = dct["data"][1]["value"][0]["dbms_version"]
            result["url"] = self.target
        if result:
            sqlmap_results.append(result)

    def option_set(self):
        pass

    def option_get(self):
        pass

    def option_list(self):
        pass

    def scan_stop(self):
        urls = self.server + "/scan/" + self.taskid + "/stop"
        stop_data = requests.get(urls)
        dct = stop_data.json()
        if dct["success"]:
            return True
        else:
            return False

    def scan_kill(self):
        urls = self.server + "/scan/" + self.taskid + "/kill"
        kill_data = requests.get(urls)
        dct = kill_data.json()
        if dct["success"]:
            return True
        else:
            return False

    def admin_list(self):
        pass

    def scan_log(self):
        pass

    def runautosql(self):
        if not self.task_new():
            return False
        # self.option_get
        if not self.scan_start():
            return False
        while True:
            # 查询任务状态
            with app.app_context():
                is_run = mongo.db.clr_ps.find_one({"clr_id": self.tasksid})
                if not is_run:
                    mongo.db.cache.remove({"tasksid":self.tasksid})
                    break
            if self.scan_status() == "running":
                time.sleep(1)
            elif self.scan_status() == "terminated":
                break
            else:
                break
            if time.time() - self.start_time > 3000:
                error = True
                self.scan_stop()
                self.scan_kill()
                break
        self.scan_data()
        self.task_delete()



class MyThread(AutoSql, threading.Thread):
    def __init__(self, server, targeturl,tasksid):
        threading.Thread.__init__(self)
        AutoSql.__init__(self, server, targeturl,tasksid)

    def run(self):
        self.runautosql()


def sqli_test(tasksid, url, urls_data,results_id):
    is_result = 0
    r_urls=deal_url_for_get(urls_data)
    start_time = datetime.now()
    results["start_time"] = start_time
    mgs="正在检测sqli漏洞...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    sqlmap_test(tasksid,r_urls)
    with app.app_context():
        sqli_vul = mongo.db.vul.find_one({"vul_name": "sqli"})
        sqli_fix = sqli_vul["fix"][0]
        sqli_level = sqli_vul["level"]
    results["tasksid"]=tasksid
    results["results_id"]=results_id
    results["url"]=url
    results["vul"]="sql注入漏洞"
    results["fix"]=sqli_fix
    results["level"]=sqli_level
    results["scan_type"] ="sqlmap"
    #处理数据并写入数据库:
    for i in sqlmap_results:
        if i["data"]:
            results["c_url"]=i["url"]
            results["dbms"]=i["dbms"]
            results["dbms_version"]=i["dbms_version"]
            results["result"]=i["data"]
            with app.app_context():
                ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
                if ps:
                    if results.get("_id"):
                        results.pop("_id")
                    print results
                    mongo.db.clrresults.insert(results)


def sqlmap_test(tasksid,urls_data):
    global sqlmap_results
    sqlmap_results = []
    with app.app_context():
        url_num=mongo.db.cache.find({"tasksid":tasksid}).count()
    urls_len = len(urls_data)
    server = "http://127.0.0.1:8775"
    threadlist = []
    threadnum = 1
    key = 1
    # 查询任务状态
    with app.app_context():
        is_run = mongo.db.clr_ps.find_one({"clr_id": tasksid})
        if not is_run:
            mongo.db.cache.remove({"tasksid": tasksid})
            return
    for url in urls_data:
        threadlist.append(MyThread(server, url,tasksid))
    for t in threadlist:
        #查询任务状态
        with app.app_context():
            is_run = mongo.db.clr_ps.find_one({"clr_id": tasksid})
            if not is_run:
                mongo.db.cache.remove({"tasksid": tasksid})
                return
        t.start()

    for t in threadlist:
        #查询任务状态
        with app.app_context():
            is_run = mongo.db.clr_ps.find_one({"clr_id": tasksid})
            if not is_run:
                mongo.db.cache.remove({"tasksid": tasksid})
                return
        p = int((float(1) / float(urls_len * 2*url_num)) * 100)
        with app.app_context():
            ps = mongo.db.clr_ps.find_one({"clr_id": tasksid})
            if ps:
                p = ps["p"] + p
            mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"p": p}})
        print p
        key += 1
        t.join()


# 对url进行二次处理
def deal_url_for_get(urls_data):
    f_urls = []
    r_urls = []
    # 对url进行二次处理
    for url in urls_data:
        if url.split("?")[0] not in f_urls:
            f_urls.append(url.split("?")[0])
            r_urls.append(url)
    return r_urls