#encoding:utf-8
from .. import app,mongo
import requests,time
from bs4 import BeautifulSoup
from datetime import datetime
from sqli_engine import sqli_test
from xss_engine import xss_test
from fl_engine import fl_test
from sensitive_engine import get_sensitive_data


def getheaders():
    headers={}
    with app.app_context():
        m_headers=mongo.db.server_fp.find_one({"type":"headers"})
        headers["User-Agent"]=m_headers["useragent"][0]
        headers["Accept-Language"]=m_headers["acceptlanguage"]
        print headers
    return headers

urls_data = []
c_urls = []



#清理source以便存储和使用
def clear_source(source):
    urls=[]
    lst=source.strip(" ").replace("\n","").split(";")
    if "" in lst:
        lst.remove("")
    urls=list(set(lst))
    return urls


#启动爬虫扫描引擎
def run_crawlerscan(urls,tasksid):
    print urls
    start_time= datetime.now()
    #将引擎状态写入数据库
    with app.app_context():
        mongo.db.clr_ps.insert({"clr_id":tasksid,"p":0,"p_run":0,"show_mgs":""})
        #扫描结果信息：
        results_id=mongo.db.info.find_one({"info":"results"})["results_num"]
        results_id+=1
        mongo.db.info.update_one({"info":"results"},{"$set":{"results_num":results_id}})
        mongo.db.clrresults_log.insert({"tasksid":tasksid,"results_id":results_id,"start_time":start_time})
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"results_id": results_id}})
    # 检查sqlmapapi引擎是否开启
    try:
        res=requests.get("http://127.0.0.1:8775")
    except:
        with app.app_context():
            mgs = "sqli引擎没有启动!请启动后进行扫描!"
            mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
        return
    collect_urls(urls,tasksid)       #启用爬虫
    urls_cache=clear_urls_for_get(tasksid)
    if urls_cache:
        for i in urls_cache:
            #检查url是否存在：
            try:
                req=requests.get(i["url"],headers=getheaders())
            except:
                mgs="远程地址:"+i["url"]+" 连接失败!请查看网络连接或者远程服务是否开启。"
                with app.app_context():
                    mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
                continue
            xss_result = {}
            sqli_result = {}
            fl_result={}
            result={}
            st_data=get_sensitive_data(i["url"],i["tasksid"],results_id)     #启动敏感数据收集引擎
            xss_test(i["tasksid"],i["url"],i["urls_data"],results_id)   #启用xss扫描引擎
            sqli_test(i["tasksid"], i["url"], i["urls_data"],results_id)  # 启用sqli扫描引擎
            if st_data.get("server_lang"):      #判断是否是php语言，如果是，启动fl扫描引擎
                if "php" in st_data.get("server_lang"):
                    fl_test(i["tasksid"],i["url"],i["urls_data"],results_id)

            end_time=datetime.now()
            #运行完成结束ps,清理缓存
            with app.app_context():
                is_run = mongo.db.clr_ps.find_one({"clr_id": tasksid})
                if is_run:
                    mongo.db.clr_ps.remove({"clr_id": tasksid})
                    mongo.db.cache.remove({"tasksid": tasksid})
                    mongo.db.clrresults_log.update_one({"results_id":results_id},{"$set":{"end_time":end_time}})
            # #对sqli结果json封装
            # with app.app_context():
            #     sqli_vul=mongo.db.vul.find_one({"vul_name":"sqli"})
            #     sqli_fix=sqli_vul["fix"][0]
            #     sqli_level=sqli_vul["level"]
            # if sqli_result.get("is_result"):
            #     sqli_results={"sqli_result":sqli_result,"fix":sqli_fix,"level":sqli_level}
            # else:
            #     sqli_result={}
            # #对xss结果json封装
            # with app.app_context():
            #     xss_vul=mongo.db.vul.find_one({"vul_name":"reflex_xss"})
            #     xss_fix=xss_vul["fix"][0]
            #     xss_level=xss_vul["level"]
            # if xss_result:
            #     xss_result={"xss_result":xss_result,"fix":xss_fix,"level":xss_level}
            # else:
            #     xss_result={}
            #对fli结果进行封装
            # if fl_result:
            #     with app.app_context():
            #         fli_vul=mongo.db.vul.find_one({"vul_name":"fli"})
            #         fli_fix=fli_vul["fix"][0]
            #         fli_level=fli_vul["level"]
            #     fl_result={"fl_result":fl_result,"fix":fli_fix,"level":fli_level}
            # result={"url":i["url"],"st_data":st_data,"sqli":sqli_result,"xss":xss_result,"fli":fl_result}
            # key=str(key)
            # results[key]=result
            # key=int(key)+1
        #
        # end_time=datetime.now()
        # clr_results={"tasksid":tasksid,"start_time":start_time,"end_time":end_time,"results":results}
        # with app.app_context():
        #     is_run=mongo.db.clr_ps.find_one({"clr_id":tasksid})
        #     if is_run:
        #         print type(clr_results)
        #         print clr_results
        #         mongo.db.clrresults.insert(clr_results)
        #         mongo.db.clr_ps.remove({"clr_id": tasksid})
        #         mongo.db.cache.remove({"tasksid":tasksid})
    # else:
    #     pass
    # print results


#收集url
def collect_urls(url_list,tasksid):
    mgs = "正在运行爬虫引擎，收集资源...."
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    st_data={}
    for url in url_list:
        try:
            req=requests.get(url,headers=getheaders())
        except:
            mgs="远程地址:"+url+" 连接失败!请查看网络连接或者远程服务是否开启。"
            with app.app_context():
                mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
            continue
        if "http:" or "https:" in url:
            collect_url(url,tasksid)
        else:
            url="http:"+url
            collect_url(url,tasksid)

def collect_url(url,tasksid):
    headers=getheaders()
    mgs=""
    global urls_data
    global c_urls
    show_mgs = {}
    http_t=url.split("/")[0]
    host=url.split("/")[0:-1]
    host="/".join(host)
    if True:
        if "https"==url.split(":")[0]:
            res=requests.get(url,verify=True,headers=headers)
        else:
            res=requests.get(url,headers=headers)
        if res:
            #使用广度遍历算法进行收集url
            crawler(url,host,http_t,headers,tasksid)
            if urls_data:
                with app.app_context():
                    mongo.db.cache.insert({"tasksid":tasksid,"url":url,"urls_data":urls_data})
            urls_data = []
            c_urls = []


#广度优先遍历
def crawler(url,host,http_t,headers,tasksid):
    try:
        if url not in c_urls:
            if "http:" in url:
                res=requests.get(url,headers=headers)
                if res.status_code=="404":
                    pass
            if "https:" in url:
                res=requests.get(url,headers=headers)
            content=res.content
            soup=BeautifulSoup(content,"lxml")
            html_a=soup.find_all("a")
            start_urls_data_len=len(urls_data)
            for li in html_a:
                #查询任务状态
                with app.app_context():
                    is_run=mongo.db.clr_ps.find_one({"clr_id":tasksid})
                    if not is_run:
                        mongo.db.cache.remove({"tasksid":tasksid})
                        return
                link=li.get("href")
                if "javascript:" in link:
                    continue
                if 'https:' in link or 'http:' in link:
                    if host not in link:
                        continue
                if http_t not in link:
                    if "/"==link[0]:
                        link=host+link
                    else:
                        link=host+"/"+link
                if link not in urls_data:
                    print link
                    urls_data.append(link)
                    crawler(link,host,http_t,headers,tasksid)
            c_urls.append(url)
            end_url_data_len=len(urls_data)
            if start_urls_data_len==end_url_data_len:
                return
        else:
            return

    except:
        pass

# #数据获取并第一次清理
# def get_ahref_url(res,host,http_t):
#     links=[]
#     content=res.content
#     soup=BeautifulSoup(content,"lxml")
#     html_a=soup.find_all("a")
#     for li in html_a:
#         link=li.get('href')
#         if host not in link:
#             continue
#         if http_t not in link:
#             link=http_t+"//"+host
#         print link
#         links.append(link)
#     return list(set(links))


# #获取敏感数据
# def get_sensitive_data(url,tasksid):
#     mgs=""
#     #从数据库获取敏感数特征库,进行特征对比
#     with app.app_context():
#         server_lang=mongo.db.server_fp.find_one({"type":"server_lang"})["feature"]
#         error_page=mongo.db.server_fp.find_one({"type":"error_page"})["feature"]
#         cookie_type = mongo.db.server_fp.find_one({"type": "cookie_type"})["feature"]
#         http_method_danger = mongo.db.server_fp.find_one({"type": "http_method_danger"})["feature"]
#         server_type=mongo.db.server_fp.find_one({"type":"server_type"})["feature"]
#     sensitive_data={}
#     try:
#         res=requests.get(url,headers=headers)
#         resheaders=res.headers
#         url=url
#         content=res.content
#     except:
#         print "获取敏感数据时，发生异常!"
#         return "error"
#
#     #获取server_type,power_by
#     mgs = "正在获取服务器信息...."
#     mgs=url+": "+mgs
#     with app.app_context():
#         mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs":mgs}})
#     if resheaders.get("Server"):
#         sensitive_data["server_type"]=resheaders.get("Server")
#     if resheaders.get("X-Powered-By"):
#         sensitive_data["server_lang"]=resheaders.get("X-Power-By")
#
#     #获取开发语言：
#     mgs="正在识别web开发语言...."
#     mgs = url + ": " + mgs
#     with app.app_context():
#         mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
#     html_doc=content
#     soup=BeautifulSoup(html_doc,"lxml")
#     html_a=soup.find_all("a")
#     links=[]
#     for l in html_a:
#         links.append(l.get('href'))
#     if not sensitive_data.get("server_lang"):
#         for language in server_lang["base_lang"]:
#             for i in links:
#                 if language in tolower(i):
#                     sensitive_data["server_lang"]=language
#     if not sensitive_data.get("server_lang"):
#         for complex in server_lang["complex_lang"]:
#             for i in server_lang["complex_lang"][complex]:
#                 for link in links:
#                     if i in tolower(link):
#                         sensitive_data["server_lang"]=i
#     if not sensitive_data.get("server_lang"):
#         for co in cookie_type:
#             if resheaders.get("Set-Cookie"):
#                 if co in tolower(resheaders.get("Set-Cokkie")):
#                     if co=="aspsession":
#                         sensitive_data["server_lang"]="asp"
#                     if co=="jsession":
#                         sensitive_data["server_lang"]="java"
#                     if co=="phpsession":
#                         sensitive_data["server_lang"]="php"
#                     if co=="jservsession":
#                         sensitive_data["server_lang"]="java"
#
#     #获取不安全的http方法
#     mgs="正在检查http方法...."
#     mgs = url + ": " + mgs
#     with app.app_context():
#         mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
#     try:
#         res=requests.options(url,headers=headers)
#         if res.headers.get("Allow"):
#             allows=res.headers.get("Allow")
#             for allow in http_method_danger:
#                 if allow in allows and not sensitive_data.get("http_method_danger"):
#                     sensitive_data["http_method_danger"]=allows
#     except:
#         pass
#
#     #初步验证cookie属性
#     mgs="初步检查cookie属性...."
#     mgs = url + ": " + mgs
#     with app.app_context():
#         mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
#     if resheaders.get("Set-Cookie"):
#         if "httponly" not in resheaders.get("Set-Cookie"):
#             sensitive_data["http_cookie_danger"]={}
#             sensitive_data["http_cookie_danger"]=(url,"not-set-httponly")
#
#     #错误页面处理
#     mgs="正在检查错误页面...."
#     mgs = url + ": " + mgs
#     with app.app_context():
#         mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
#     s=""
#     for _ in range(5):
#         s+=random.choice(string.ascii_letters+string.digits)
#     urla=url+"/"+s
#     try:
#         res=requests.get(urla,headers=headers)
#         content=res.content
#         for error in error_page:
#             if error in tolower(content):
#                 sensitive_data["error_page"]=error
#         #
#         # for server_t in server_type:
#         #     if server_t in tolower(content):
#         #         sensitive_data["server_type"]=server_t
#     except:
#         pass
#     return sensitive_data


# def xss_test(tasksid,url,urls_data):
#     pass
#
#
# def sqli_test(tasksid,url,urls_data):
#     #custom_sqli_test()
#     sqlmapapi_test()
#     pass
#
#
# def sqlmapapi_test():
#     pass
#
# def fl_test():
#     pass


#清理urls,获取常规get请求
def clear_urls_for_get(tasksid):
    urls_cache=[]
    with app.app_context():
        cache=mongo.db.cache.find({"tasksid":tasksid})
    for i in cache:
        cls_url = []
        for url in i["urls_data"]:
            if "?" not in url:
                continue
            cls_url.append(url)
        urls_cache.append({"tasksid":tasksid,"url":i["url"],"urls_data":cls_url})
    return urls_cache

