#encoding:utf-8
from .. import app,mongo
import random,string,requests
import re

xss_result=[]
xss_results_dct={}

def getheaders():
    headers={}
    with app.app_context():
        m_headers=mongo.db.server_fp.find_one({"type":"headers"})
        headers["User-Agent"]=m_headers["useragent"][0]
        headers["Accept-Language"]=m_headers["acceptlanguage"]
        print headers
    return headers


def xss_test(tasksid,url,urls_data,results_id):
    global xss_results_dct,xss_result
    xss_result = []
    xss_results_dct = {}
    mgs="正在检测xss漏洞...."
    mgs = url + ": " + mgs
    with app.app_context():
        mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"show_mgs": mgs}})
    xss_reflex(tasksid,url,urls_data,results_id)
    return xss_results_dct


#反射型xss
def xss_reflex(tasksid,url,urls_data,results_id):
    global xss_result
    results={}
    flag=0
    with app.app_context():
        url_num=mongo.db.cache.find({"tasksid":tasksid}).count()
        #取出xss信息
        xss_vul = mongo.db.vul.find_one({"vul_name": "reflex_xss"})
        xss_fix = xss_vul["fix"][0]
        xss_level = xss_vul["level"]

    #处理results:
    results["tasksid"]=tasksid
    results["url"]=url
    results["vul"] = "xss漏洞"
    results["fix"]=xss_fix
    results["level"]=xss_level
    results["scan_type"] ="custom"
    results["results_id"]=results_id
    key=1
    r_urls = deal_url_for_get(urls_data)
    urls_len = len(r_urls)
    for i_url in r_urls:
        #查询任务状态
        with app.app_context():
            is_run = mongo.db.clr_ps.find_one({"clr_id": tasksid})
            if not is_run:
                mongo.db.cache.remove({"tasksid": tasksid})
                return
        xss_url(i_url)
        p = int((float(1) / float(urls_len * 2*url_num)) * 100)  #一个单元
        with app.app_context():
            ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
            if ps:
                p=ps["p"]+p
            mongo.db.clr_ps.update_one({"clr_id": tasksid}, {"$set": {"p": p}})
            print p
        #将结果存入数据库：
        if xss_result:
            results["result"]=xss_result
            results["c_url"]=i_url
            with app.app_context():
                ps=mongo.db.clr_ps.find_one({"clr_id":tasksid})
                if ps:
                    if results.get("_id"):
                        results.pop("_id")
                    print results
                    mongo.db.clrresults.insert(results)
            xss_result=[]
    print "xss_r"

#数据处理，xss验证
def xss_url(i_url):
    #拆解get_url,插入payload后,进行简单xss_reflex判断
    args_dct={}
    url=""
    headers=getheaders()
    args_dct=add_payload(i_url)
    url = i_url.split("?")[0]
    args=[]
    if args_dct:
        for i in args_dct:    #对get参数依次验证
            c_str = args_dct[i]
            payload=make_random_str()
            args_dct[i] = payload
            arg = ""
            for k in args_dct:
                arg = k + "=" + args_dct[k]
                args.append(arg)
            carry_payload_url=url + "?" + "&".join(args)
            is_xss=first_verify_xss(carry_payload_url,payload,headers)
            args_dct[i] = c_str
            if is_xss:
                again_verify_xss(args_dct,url,headers)

def make_random_str():
    #生成随机字符串len=4
    s=""
    for _ in range(5):
        s+=random.choice(string.ascii_letters+string.digits)
    return s


def first_verify_xss(carry_payload_url,payload,headers):
    is_xss=False
    try:
        res=requests.get(carry_payload_url,headers=headers)
        content=res.content
        if payload in content:
            is_xss=True
            return is_xss
    except:
        return is_xss


def again_verify_xss(args_dct,url,headers):
    spal_char=["'","\"","<",">"]
    with app.app_context():
        xss_reflex_payload=mongo.db.xss.find_one({"type":"reflex_payload"})["payload"]
        jsevent=mongo.db.xss.find_one({"type":"reflex_payload"})["jsevent"]
    #进行单引号验证
    args=[]
    if args_dct:
        for i in args_dct:  # 对get参数依次验证
            c_str = args_dct[i]
            payload = make_random_str()
            args_dct[i] = payload
            arg = ""
            for k in args_dct:
                arg = k + "=" + args_dct[k]
                args.append(arg)
            carry_payload_url = url + "?" + "&".join(args)
            res=requests.get(carry_payload_url,headers=headers)
            content=res.content
            if payload in content:
                pattern_sqm = "['][\s\w]*" + payload
                pattern_dqm = "[\"][\s\w]*" + payload
                pattern_ab = "[>][\s\w]*" + payload

                # 在html标签内或者在js代码内的单引号
                r = re.search(pattern_sqm, content, re.M | re.I)
                if r:
                    sqm_payload = payload + spal_char[0] + payload
                    args_dct[i] = sqm_payload
                    arg = ""
                    args=[]
                    for k in args_dct:
                        arg = k + "=" + args_dct[k]
                        args.append(arg)
                    carry_payload_url = url + "?" + "&".join(args)
                    res = requests.get(carry_payload_url, headers=headers)
                    content = res.content
                    if sqm_payload in content:
                        sqm_m_payload = xss_reflex_payload[6]
                        sqm_m_payload=sqm_m_payload.replace("[JSEVENT]", random.choice(jsevent))
                        sqm_m_payload=sqm_m_payload.replace("[RANDSTR]", make_random_str())
                        args_dct[i] = sqm_m_payload
                        arg = ""
                        args=[]
                        for k in args_dct:
                            arg = k + "=" + args_dct[k]
                            args.append(arg)
                        carry_payload_url = url + "?" + "&".join(args)
                        res = requests.get(carry_payload_url, headers=headers)
                        content = res.content
                        if sqm_m_payload in content:
                            xss_result.append(carry_payload_url)
                # 在html标签内或者在js代码内的双引号
                r = re.search(pattern_dqm, content, re.M | re.I)
                if r:
                    dqm_payload = payload + spal_char[1] + payload
                    args_dct[i] = dqm_payload
                    arg = ""
                    args=[]
                    for k in args_dct:
                        arg = k + "=" + args_dct[k]
                        args.append(arg)
                    carry_payload_url = url + "?" + "&".join(args)
                    res = requests.get(carry_payload_url, headers=headers)
                    content = res.content
                    if dqm_payload in content:
                        dqm_m_payload = xss_reflex_payload[7]
                        dqm_m_payload=dqm_m_payload.replace("[JSEVENT]", random.choice(jsevent))
                        dqm_m_payload=dqm_m_payload.replace("[RANDSTR]", make_random_str())
                        args_dct[i] = dqm_m_payload
                        arg = ""
                        for k in args_dct:
                            arg = k + "=" + args_dct[k]
                            args.append(arg)
                        carry_payload_url = url + "?" + "&".join(args)
                        res = requests.get(carry_payload_url, headers=headers)
                        content = res.content
                        if dqm_m_payload in content:
                            xss_result.append(carry_payload_url)
                # 在html标签内或者在js代码内的尖括号
                r = re.search(pattern_ab, content, re.M | re.I)
                if r:
                    ab_payload = payload + spal_char[3] + spal_char[2] + payload
                    args_dct[i] = ab_payload
                    arg = ""
                    args=[]
                    for k in args_dct:
                        arg = k + "=" + args_dct[k]
                        args.append(arg)
                    carry_payload_url = url + "?" + "&".join(args)
                    args=[]
                    res = requests.get(carry_payload_url, headers=headers)
                    content = res.content
                    if ab_payload in content:
                        xss_reflex_payload_ab = xss_reflex_payload
                        xss_reflex_payload_ab.pop(6)
                        xss_reflex_payload_ab.pop(7)
                        ab_m_payload=random.choice(xss_reflex_payload_ab)
                        ab_m_payload=ab_m_payload.replace("[RANDSTR]", make_random_str())
                        args_dct[i] = ab_m_payload
                        arg = ""
                        for k in args_dct:
                            arg = k + "=" + args_dct[k]
                            args.append(arg)
                        carry_payload_url = url + "?" + "&".join(args)
                        res = requests.get(carry_payload_url, headers=headers)
                        content = res.content
                        if ab_m_payload in content:
                            xss_result.append(carry_payload_url)


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

#对args参数处理成字典
def add_payload(i_url):
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
    return args_dct