from flask import Flask,Blueprint
import os
from flask_pymongo import PyMongo
import sys

app=Flask(__name__)

app.secret_key=os.urandom(24)

app.config["MONGO_DBNAME"]="luescan"
app.config["MONGO_HOST"]="127.0.0.1"
app.config["MONGO_PORT"]=27017
#app.config["MONGO_USERNAME"]="root"
#app.config["MONGO_PASSWORD"]="root"
app.config["loginuser"]="root"
app.config["loginpwd"]="root"


plugin=Blueprint("plugin",__name__)
crawler=Blueprint("crawler",__name__)

sys.path.append(sys.path[0]+"\\views\\lib\\sqlmap\\")

sys.path.append(sys.path[0]+"\\views\\lib\\fimap\\src\\")

mongo=PyMongo(app,config_prefix="MONGO")
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append(sys.path[0]+"\\vuldb\\")
file_path=sys.path[-1]
print file_path