#encoding:utf-8
from .fimap.src.fimapapi import fimapapi
from .. import app,mongo
from datetime import datetime

keyword=["url","file","header","foot","page","f","p"]

def fl_test(tasksid,url,urls_data,results_id):
    results={}
    with app.app_context():
        fli_vul = mongo.db.vul.find_one({"vul_name": "fli"})
        fli_fix = fli_vul["fix"][0]
        fli_level = fli_vul["level"]

    results["tasksid"]=tasksid
    results["results_id"]=results_id
    results["url"]=url
    results["vul"] = "php文件包含漏洞"
    results["fix"]=fli_fix
    results["level"]=fli_level
    results["scan_type"] ="fimap"
    start_time = datetime.now()
    results["start_time"] = start_time

    #fl_test_custom(urls_data,tasksid)
    mgs="正在检测fli漏洞...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    result=fl_test_fimap(urls_data,tasksid)
    if result:
        for i in result:
            results["c_url"]=result[i]["c_url"]
            results["result"]=result[i]["result"]
            with app.app_context():
                ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
                if ps:
                    if results.get("_id"):
                        results.pop("_id")
                    print results
                    mongo.db.clrresults.insert(results)
    print "fl_test"

def fl_test_custom(urls_data,tasksid):
    #处理url，是否lf判断
    r_urls=deal_url_for_get(urls_data)
    for i_url in r_urls:
        is_fl=deal_url_fl(i_url)
        if is_fl:
            #远程文件包含判断
            is_rfl=is_rfl_test(i_url)
            #本地文件包含判断
            is_lfl=is_lfl_test(i_url)


def fl_test_fimap(urls_data,tasksid):
    result_list=[]
    results={}
    r_urls=deal_url_for_get(urls_data)
    key=0

    for i_url in r_urls:
        #查询任务状态
        with app.app_context():
            is_run = mongo.db.clr_ps.find_one({"clr_id": tasksid})
            if not is_run:
                mongo.db.cache.remove({"tasksid": tasksid})
                return
        result_list=fimapapi(i_url)
        if result_list:
            key=str(key)
            results[key]={"c_url":i_url,"result":result_list}
            key=int(key)+1
    return results

def is_rfl_test(i_url):
    pass

def is_lfl_test(i_url):
    pass

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

#处理url进行关键字判断
def deal_url_fl(i_url):
    args_dct={}
    args=[]
    if "?" in i_url:
        url=i_url.split("?")[0]  #不携带get数据的url
        if "&" in i_url.split("?")[1]:
            args=[i for i in i_url.split("?")[1].split("&")]
            for i in args:
                if "=" in i:
                    key = i.split("=")[0]
                    value = i.split("=")[1]
                    if key and value:
                        args_dct[key] = value
        else:
            if "=" in i_url.split("?")[1]:
                args=i_url.split("?")[1]
                key=args.split("=")[0]
                value=args.split("=")[1]
                if key and value:
                    args_dct[key]=value
    is_fl=False
    for arg in args_dct:
        if arg in keyword:
            is_fl=True
        else:
            is_fl=False
    return is_fl


