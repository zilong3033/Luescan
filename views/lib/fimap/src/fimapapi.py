#encoding:utf-8


'''
简单接口，用于外部调用。
大部分功能没有接口，只对singleScan进行处理。
'''

from baseClass import baseClass
from targetScanner import targetScanner
import sys, time
import language
from plugininterface import plugininterface


class singleScan(baseClass):

    def _load(self):
        self.URL = None
        self.quite = False

    def setURL(self, URL):
        self.URL = URL

    def setQuite(self, b):
        self.quite = b

    def scan(self):
        boxarr = []
        try:
            self.localLog("SingleScan is testing URL: '%s'" % self.URL)
            t = targetScanner(self.config)
            t.MonkeyTechnique = self.config["p_monkeymode"]

            idx = 0
            if (t.prepareTarget(self.URL)):
                res = t.testTargetVuln()
                if (len(res) == 0):
                    self.localLog("Target URL isn't affected by any file inclusion bug :(")
                else:
                    for i in res:
                        report = i[0]
                        files = i[1]
                        idx = idx + 1
                        boxarr = []
                        header = "[%d] Possible File Inclusion" % (idx)
                        if (report.getLanguage() != None):
                            header = "[%d] Possible %s-File Inclusion" % (idx, report.getLanguage())
                        boxarr.append("::REQUEST")
                        boxarr.append("  [URL]        %s" % report.getURL())
                        if (report.getPostData() != None and report.getPostData() != ""): boxarr.append(
                            "  [POST]       %s" % report.getPostData())
                        if (report.getHeader() != None and report.getHeader().keys() > 0):
                            modkeys = ",".join(report.getHeader().keys())
                            boxarr.append("  [HEAD SENT]  %s" % (modkeys))

                        boxarr.append("::VULN INFO")
                        if (report.isPost == 0):
                            boxarr.append("  [GET PARAM]  %s" % report.getVulnKey())
                        elif (report.isPost == 1):
                            boxarr.append("  [POSTPARM]   %s" % report.getVulnKey())
                        elif (report.isPost == 2):
                            boxarr.append("  [VULN HEAD]  %s" % report.getVulnHeader())
                            boxarr.append("  [VULN PARA]  %s" % report.getVulnKey())

                        if (report.isBlindDiscovered()):
                            boxarr.append("  [PATH]       Not received (Blindmode)")
                        else:
                            boxarr.append("  [PATH]       %s" % report.getServerPath())
                        if (report.isUnix()):
                            boxarr.append("  [OS]         Unix")
                        else:
                            boxarr.append("  [OS]         Windows")

                        boxarr.append("  [TYPE]       %s" % report.getType())
                        if (not report.isBlindDiscovered()):
                            if (report.isSuffixBreakable() == None):
                                boxarr.append("  [TRUNCATION] No Need. It's clean.")
                            else:
                                if (report.isSuffixBreakable()):
                                    boxarr.append(
                                        "  [TRUNCATION] Works with '%s'. :)" % (report.getSuffixBreakTechName()))
                                else:
                                    boxarr.append("  [TRUNCATION] Doesn't work. :(")
                        else:
                            if (report.isSuffixBreakable()):
                                boxarr.append("  [TRUNCATION] Is needed.")
                            else:
                                boxarr.append("  [TRUNCATION] Not tested.")
                        boxarr.append("  [READABLE FILES]")
                        if (len(files) == 0):
                            boxarr.append("                     No Readable files found :(")
                        else:
                            fidx = 0
                            for file in files:
                                payload = "%s%s%s" % (report.getPrefix(), file, report.getSurfix())
                                if (file != payload):
                                    if report.isWindows() and file[1] == ":":
                                        file = file[3:]
                                    txt = "                   [%d] %s -> %s" % (fidx, file, payload)
                                    # if (fidx == 0): txt = txt.strip()
                                    boxarr.append(txt)
                                else:
                                    txt = "                   [%d] %s" % (fidx, file)
                                    # if (fidx == 0): txt = txt.strip()
                                    boxarr.append(txt)
                                fidx = fidx + 1
                        self.drawBox(header, boxarr)
        except KeyboardInterrupt:
            if (self.quite):  # We are in google mode.
                print "\nCancelled current target..."
                print "Press CTRL+C again in the next second to terminate fimap."
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    raise
            else:  # We are in single mode. Simply raise the exception.
                raise

        return boxarr

    def localLog(self, txt):
        if (not self.quite):
            print txt



def fimapapi(p_url):
    result=[]
    config={'p_doDotTruncation': False, 'p_dot_trunc_step': 50, 'p_googlesleep': 5, 'p_rfi_encode': None, 'p_pages': 10, 'p_monkeymode': False, 'p_depth': 1, 'p_list': None, 'p_proxy': None, 'p_mode': 0, 'p_skiponerror': False,'p_query': None, 'p_dot_trunc_only_win': True, 'header': {}, 'p_exploit_domain': None, 'force-run': False, 'p_exploit_script_id': None, 'p_exploit_payload': None, 'p_dot_trunc_min': 700, 'p_multiply_term': 1, 'force-os': None, 'p_dot_trunc_ratio': 0.095, 'p_write': None, 'p_verbose': 2, 'p_dot_trunc_max': 2000, 'p_ttl': 30, 'p_skippages': 0, 'p_useragent': 'fimap.googlecode.com/v1.00_svn (My life for Aiur)', 'p_post': '', 'p_maxtries': 5, 'p_results_per_query': 100, 'p_color': False, 'p_bingkey': None, 'p_mergexml': None, 'p_exploit_filter': '', 'p_exploit_cmds': None, 'p_tabcomplete': False,'p_autolang': True}
    config["p_url"]=p_url
    xmlsettings = language.XML2Config(config)
    config["XML2CONFIG"] = xmlsettings
    plugman = plugininterface(config)
    config["PLUGINMANAGER"] = plugman
    if (config["p_mode"] == 0):
        single = singleScan(config)
        single.setURL(config["p_url"])
        result=single.scan()
    return result


# fimapapi("http://127.0.0.1:88/sqlgun/sqlgun/fltest.php?file=xss.php")
# print sys.path[0]