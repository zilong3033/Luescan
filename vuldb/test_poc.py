#encoding:utf-8

def plugin_info():
    plugin_info={"name":"xss漏洞","info":"cms sql注入漏洞的影响范围很广请注意及时修复","level":"高危","source":{"official":0,"changeid":0},"author":"zilong","url":"http://zilong3033.cn","type":"sql注入漏洞","keywords":"cms"}
    return plugin_info
    
def check(url):
    return url+" 存在xss漏洞!"
