from views.view import app
from views.crawler_view import crawler
from views.plugin_view import plugin
#from views.lib.sqlmap.sqlmapapi import sqlmap_server
#import multiprocessing

app.register_blueprint(crawler)
app.register_blueprint(plugin)

if __name__=="__main__":
    #t = multiprocessing.Process(target=sqlmap_server, args=())
    #t.start()
    app.debug=True
    app.run(threaded=True,host="127.0.0.1",port=80)