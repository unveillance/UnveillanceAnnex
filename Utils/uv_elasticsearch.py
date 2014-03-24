import subprocess, os, json, re
from sys import argv
from time import sleep

from lib.Core.Utils.funcs import stopDaemon, startDaemon
from Utils.funcs import printAsLog
from conf import MONITOR_ROOT, CONF_ROOT, ELS_ROOT

from lib.Core.Utils.uv_elasticsearch import UnveillanceElasticsearch as UVE_Stub

class UnveillanceElasticsearch(UVE_Stub):
	def __init__(self):
		super(UnveillanceElasticsearch, self).__init__()
		
		self.els_status_file = os.path.join(MONITOR_ROOT, "els.status.txt")
		self.els_pid_file = os.path.join(MONITOR_ROOT, "els.pid.txt")
		self.els_log_file = os.path.join(MONITOR_ROOT, "els.log.txt")
		
		self.first_use = False
		if argv[1] == "-firstuse": self.first_use = True
		
	def startElasticsearch(self, catch=True):
		startDaemon(self.els_log_file, self.els_pid_file)
		
		cmd = [ELS_ROOT, '-Des.max-open-files=true', 
			'Des.config=%s' % os.path.join(CONF_ROOT, "els.settings.yaml")]
		
		print "elasticsearch running in daemon."
		print cmd
		
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
		data = p.stdout.readline()
	
		while data:
			print data
			if re.match(r'.*started$', data):
				print "STARTED: %s" % data
				self.status = True
				with open(self.els_status_file, 'wb+') as f: f.write("True")
				sleep(1)
				
				self.first_use: self.initElasticsearch()
				break
		
			data = p.stdout.readline()
		p.stdout.close()
		
		if catch:
			while True: sleep(1)
	
	def stopElasticsearch(self):
		printAsLog("stopping elasticsearch")
		stopDaemon(self.els_pid_file)
		
		self.status = False
		with open(self.els_status_file, 'wb+') as f: f.write("False")
	
	def initElasticsearch(self):
		print "INITING ELASTICSEARCH"
		mappings = {
			"documents" : {
				"properties": {
					"assets": {
						"type" : "nested",
						"include_in_parent": True,
						"include_in_root": True
					}
				}
			}
		}
		
		index = {'mappings': mappings}
		
		try:
			res = self.sendELSRequest(to_root=True, method="delete")
			if res['error'] == "IndexMissingException[[compass] missing]": pass
		except KeyError as e: pass
		
		print "DELETED OLD MAPPING:"
		print res
		
		try:
			res = self.sendELSRequest(data=index, to_root=True, method="put")
			print "INITIALIZED NEW MAPPING:"
			print res
			
			if not res['acknowledged']: return False
					
		except Exception as e:
			printAsLog(e, as_error=True)
			return False
		
	def delete(self, _id):
		print "deleting thing"
		if not self.status: return False
		
		res = self.sendELSRequest(endpoint=_id, method="delete")
		
		try: return res['ok']
		except KeyError as e: pass
		
		return False
	
	def sendELSRequest(self, data=None, to_root=False, endpoint=None, method="get"):
		url = "http://localhost:9200/unveillance/"

		if not to_root:
			url += "documents/"
			if endpoint is not None:
				url += endpoint
		
		if data is not None:
			data = json.dumps(data)
			
		if method == "get":
			r = requests.get(url, data=data)
		elif method == "post":
			r = requests.post(url, data=data)
		elif method == "put":
			r = requests.post(url, data=data)
		elif method == "delete":
			r = requests.delete(url, data=data)
		
		return json.loads(r.content)