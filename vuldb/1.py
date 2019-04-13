#encoding:utf-8
def plugin_info():
    return "test_1"

def check(url):
    return url+" 存在sql注入漏洞!"
