#encoding:utf-8

def plugin_info():
    plugin_info={"name":"weblogic反序列化漏洞","info":"weblogic10.5.4反序列化漏洞","level":"高危","source":{"official":0,"changeid":0},"author":"zilong","url":"http://zilong3033.cn","type":"java 反序列化漏洞","keywords":"weblogic,反序列化漏洞,java"}
    return plugin_info
    
def check(url):
    return url+" 存在反序列化漏洞!"
