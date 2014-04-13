import subprocess, os, json, re, requests
from sys import argv
from time import sleep

from lib.Core.Utils.funcs import stopDaemon, startDaemon
from Utils.funcs import printAsLog
from conf import MONITOR_ROOT, CONF_ROOT, ELS_ROOT, DEBUG

class UnveillanceElasticsearchHandler(object):
	def __init__(self):
		if DEBUG: print "elasticsearch handler inited"
		
	def get(self, _id):
		if DEBUG: print "getting thing"
		res = self.sendELSRequest(endpoint=_id)
		try:
			if res['found']: return res['_source']
		except KeyError as e: pass
		
		return None
	
	def query(self, args, count_only=False):
		if DEBUG: 
			print "OH A QUERY"
			print args
		
		query = {
			'query' : args,
			'from' : 0,
			'size' : 50,
			'sort' : [{"uv_document.date_added" : {"order" : "desc"}}]
		}
		
		res = self.sendELSRequest(endpoint="_search", data=query, method="post")
		if DEBUG: print res
		
		try:
			if len(res['hits']['hits']) > 0:
				if count_only: return res['hits']['total']
				else: 
					return { 
						'count' : res['hits']['total'], 
						'documents' : [h['_source'] for h in res['hits']['hits']]
					}
	
		except Exception as e:
			if DEBUG: print "ERROR ON SEARCH:\n%s" % e
		
		return None
	
	def update(self, _id, args):
		if DEBUG: print "updating thing"
		
		res = self.sendELSRequest(endpoint=_id, data=args, method="put")

		try: return res['ok']
		except KeyError as e: pass
		
		return False
	
	def create(self, _id, args):
		if DEBUG: print "creating thing"
		return self.update(_id, args)
		
	def delete(self, _id):
		if DEBUG: print "deleting thing"
		
		res = self.sendELSRequest(endpoint=_id, method="delete")
		
		try: return res['ok']
		except KeyError as e: pass
		
		return False
	
	def sendELSRequest(self, data=None, to_root=False, endpoint=None, method="get"):
		url = "http://localhost:9200/unveillance/"

		if not to_root: url += "uv_document/"
		if endpoint is not None: url += endpoint
		if data is not None: data = json.dumps(data)
		if DEBUG: 
			print data
			print url
			
		if method == "get":
			r = requests.get(url, data=data)
		elif method == "post":
			r = requests.post(url, data=data)
		elif method == "put":
			r = requests.put(url, data=data)
		elif method == "delete":
			r = requests.delete(url, data=data)
		
		return json.loads(r.content)

class UnveillanceElasticsearch(UnveillanceElasticsearchHandler):
	def __init__(self):		
		self.els_status_file = os.path.join(MONITOR_ROOT, "els.status.txt")
		self.els_pid_file = os.path.join(MONITOR_ROOT, "els.pid.txt")
		self.els_log_file = os.path.join(MONITOR_ROOT, "els.log.txt")
		
		self.first_use = False
		if argv[1] == "-firstuse": self.first_use = True
		
		UnveillanceElasticsearchHandler.__init__(self)
		
	def startElasticsearch(self, catch=True):
		cmd = [ELS_ROOT, '-Des.max-open-files=true', 
			'-Des.config=%s' % os.path.join(CONF_ROOT, "els.settings.yaml")]
		
		print "elasticsearch running in daemon."
		print cmd
		
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
		data = p.stdout.readline()
	
		while data:
			print data
			if re.match(r'.*started$', data):
				print "STARTED: %s" % data
				with open(self.els_status_file, 'wb+') as f: f.write("True")
				sleep(1)
				
				if self.first_use: self.initElasticsearch()
				break
		
			data = p.stdout.readline()
		p.stdout.close()
		
		startDaemon(self.els_log_file, self.els_pid_file)
		if catch:
			while True: sleep(1)
	
	def stopElasticsearch(self):
		printAsLog("stopping elasticsearch")
		stopDaemon(self.els_pid_file)
		
		with open(self.els_status_file, 'wb+') as f: f.write("False")
	
	def initElasticsearch(self):
		if DEBUG: print "INITING ELASTICSEARCH"
		mappings = {
			"uv_document" : {
				"properties": {
					"uv_type": {
						"type" : "string",
						"store" : True
					},
					"assets": {
						"type" : "nested",
						"include_in_parent": True,
						"include_in_root": True
					}
				}
			}
		}
		
		index = { "mappings": mappings }

		try:
			res = self.sendELSRequest(to_root=True, method="delete")
			
			if DEBUG:
				print "DELETED OLD MAPPING:"
				print res
		except Exception as e: 
			if DEBUG: print e
			printAsLog(e, as_error=True)
				
		try:
			res = self.sendELSRequest(data=index, to_root=True, method="put")
			if DEBUG:
				print "INITIALIZED NEW MAPPING:"
				print res
			
			if not res['acknowledged']: return False
					
		except Exception as e:
			printAsLog(e, as_error=True)
			return False