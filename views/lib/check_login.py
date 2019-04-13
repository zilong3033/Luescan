#encoding:utf-8
from functools import wraps
from flask import url_for,session,redirect

#登录检查:
def checklogin(f):
    @wraps(f)
    def warpper(*args,**kwargs):
        try:
            if "login" in session:
                if session["login"]=="login_success":
                    return f(*args,**kwargs)
                else:
                    return redirect(url_for("Login"))
            else:
                return redirect(url_for("Login"))
        except Exception,e:
            print e
            print "checklogin"
            return redirect(url_for("Error"))

    return warpper