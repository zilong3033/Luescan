#encoding:utf-8
from .. import app,mongo
from bs4 import BeautifulSoup
import requests,string,random
from datetime import datetime

def getheaders():
    headers={}
    with app.app_context():
        m_headers=mongo.db.server_fp.find_one({"type":"headers"})
        headers["User-Agent"]=m_headers["useragent"][0]
        headers["Accept-Language"]=m_headers["acceptlanguage"]
        print headers
    return headers


#数据转化为小写，以便字符串处理
def tolower(data):
    if data:
        if type(data)==type([]):
            tolower_data=[]
            for i in data:
                d=tolower(i)
                tolower_data.append(d)
            return tolower_data
        if type(data)==type({}):
            tolower_data={}
            for i in data:
                d=tolower(i)
                values=tolower(data[i])
                tolower_data[d]=values
            return tolower_data
        if type(data)==type(""):
            return data.lower()
    else:
        return 0


#获取敏感数据
def get_sensitive_data(url,tasksid,results_id):
    headers=getheaders()
    mgs=""
    #从数据库获取敏感数特征库,进行特征对比
    with app.app_context():
        server_lang=mongo.db.server_fp.find_one({"type":"server_lang"})["feature"]
        error_page=mongo.db.server_fp.find_one({"type":"error_page"})["feature"]
        cookie_type = mongo.db.server_fp.find_one({"type": "cookie_type"})["feature"]
        http_method_danger = mongo.db.server_fp.find_one({"type": "http_method_danger"})["feature"]
        server_type=mongo.db.server_fp.find_one({"type":"server_type"})["feature"]
    sensitive_data={}
    try:
        res=requests.get(url,headers=headers)
        resheaders=res.headers
        url=url
        content=res.content
    except:
        print "获取敏感数据时，发生异常!"
        return "error"

    #获取server_type,power_by
    mgs = "正在获取服务器信息...."
    mgs=url+": "+mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs":mgs}})
    if resheaders.get("Server"):
        sensitive_data["server_type"]=resheaders.get("Server")
    if resheaders.get("X-Powered-By"):
        sensitive_data["server_lang"]=resheaders.get("X-Power-By")

    #获取开发语言：
    mgs="正在识别web开发语言...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    html_doc=content
    soup=BeautifulSoup(html_doc,"lxml")
    html_a=soup.find_all("a")
    links=[]
    for l in html_a:
        links.append(l.get('href'))
    if not sensitive_data.get("server_lang"):
        for language in server_lang["base_lang"]:
            for i in links:
                if language in tolower(i):
                    sensitive_data["server_lang"]=language
    if not sensitive_data.get("server_lang"):
        for complex in server_lang["complex_lang"]:
            for i in server_lang["complex_lang"][complex]:
                for link in links:
                    if i in tolower(link):
                        sensitive_data["server_lang"]=i
    if not sensitive_data.get("server_lang"):
        for co in cookie_type:
            if resheaders.get("Set-Cookie"):
                if co in tolower(resheaders.get("Set-Cokkie")):
                    if co=="aspsession":
                        sensitive_data["server_lang"]="asp"
                    if co=="jsession":
                        sensitive_data["server_lang"]="java"
                    if co=="phpsession":
                        sensitive_data["server_lang"]="php"
                    if co=="jservsession":
                        sensitive_data["server_lang"]="java"

    #获取不安全的http方法
    mgs="正在检查http方法...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    try:
        res=requests.options(url,headers=headers)
        if res.headers.get("Allow"):
            allows=res.headers.get("Allow")
            for allow in http_method_danger:
                if allow in allows and not sensitive_data.get("http_method_danger"):
                    sensitive_data["http_method_danger"]=allows
    except:
        pass

    #初步验证cookie属性
    mgs="初步检查cookie属性...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    if resheaders.get("Set-Cookie"):
        if "httponly" not in resheaders.get("Set-Cookie"):
            sensitive_data["http_cookie_danger"]={}
            sensitive_data["http_cookie_danger"]=(url,"not-set-httponly")

    #错误页面处理
    mgs="正在检查错误页面...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    s=""
    for _ in range(5):
        s+=random.choice(string.ascii_letters+string.digits)
    urla=url+"/"+s
    try:
        res=requests.get(urla,headers=headers)
        content=res.content
        for error in error_page:
            if error in tolower(content):
                sensitive_data["error_page"]=error
        #
        # for server_t in server_type:
        #     if server_t in tolower(content):
        #         sensitive_data["server_type"]=server_t
    except:
        pass

    #将结果存入数据库:
    save_st(tasksid,url,sensitive_data,results_id)
    return sensitive_data


def save_st(tasksid,url,sensitive_data,results_id):
    results={}
    results["tasksid"]=tasksid
    results["results_id"]=results_id
    results["url"]=url
    results["vul"] = "威胁情报信息"
    results["scan_type"] ="custom"
    start_time = datetime.now()
    results["start_time"] = start_time
    if sensitive_data:
        results["c_url"]=url
        results["result"]=sensitive_data
        results["level"]="低危"
    with app.app_context():
        ps = mongo.db.clr_ps.find_one({"clr_id": tasksid})
        if ps:
            if results.get("_id"):
                results.pop("_id")
            print results
            mongo.db.clrresults.insert(results)