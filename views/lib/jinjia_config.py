from .. import app
import base64,hashlib
from bson.objectid import ObjectId
env=app.jinja_env

def debase64(arg):
    return base64.b64decode(arg)

def lgth(arg):
    return len(arg)

def enbase64(arg):
    return base64.b64encode(arg)

def mdfive(arg):
    h1=hashlib.md5()
    h1.update(arg.encode(encoding='utf-8'))
    return h1.hexdigest()

env.filters["debase64"]=debase64
env.filters["lgth"]=lgth
env.filters["enbase64"]=enbase64
env.filters["mdfive"]=mdfive