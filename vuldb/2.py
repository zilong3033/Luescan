#encoding:utf-8
def plugin_info():
    return "test_1"

def check(host,port):
    return host+":"+str(port)+" 存在盲注漏洞!"
