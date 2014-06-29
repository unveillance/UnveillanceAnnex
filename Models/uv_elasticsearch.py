import os, json, re, requests, urllib
from subprocess import Popen, PIPE
from crontab import CronTab
from sys import argv
from time import sleep
from fabric.api import local, settings

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
	
	def query(self, args, count_only=False, limit=None, sort=None, from_=None):
		# TODO: ACTUALLY, I MEAN ALL OF THEM.
		if limit is None: limit = 50
		if from_ is None: from_ = 0

		if sort is None: sort = [{"uv_document.date_added" : {"order" : "desc"}}]
		else:
			if type(sort) is not list: sort = [sort]
		
		query = {
			'query' : json.loads(urllib.unquote(json.dumps(args))),
			'from' : from_,
			'size' : limit,
			'sort' : sort
		}
		
		if DEBUG: 
			print "OH A QUERY"
			print query
		
		res = self.sendELSRequest(endpoint="_search", data=query, method="post")
		
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
		if DEBUG: print res
		
		try: return res['ok']
		except KeyError as e: pass
		
		return False
	
	def sendELSRequest(self, data=None, to_root=False, endpoint=None, method="get"):
		url = "http://localhost:9200/unveillance/"

		if not to_root: url += "uv_document/"
		if endpoint is not None: url += endpoint
		if data is not None: data = json.dumps(data)

		if DEBUG: print "SENDING ELS REQUEST TO %s" % url
			
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
		
		p = Popen(cmd, stdout=PIPE, close_fds=True)
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
		self.startCronJobs()

		if self.first_use:
			try:
				with open(os.path.join(CONF_ROOT, "initial_tasks.json"), 'rb') as IT:
				
					from lib.Worker.Models.uv_task import UnveillanceTask
					for i_task in json.loads(IT.read()):
						task = UnveillanceTask(inflate=i_task)
						task.run()

			except Exception as e:
				if DEBUG: print "No initial tasks...\n%s" % e
			
		if catch:
			while True: sleep(1)
	
	def stopElasticsearch(self):
		printAsLog("stopping elasticsearch")

		self.stopCronJobs()
		
		p = Popen(['lsof', '-t', '-i:9200'], stdout=PIPE, close_fds=True)
		data = p.stdout.readline()
		
		while data:			
			p_ = Popen(['kill', data.strip()])
			p_.wait()
			
			data = p.stdout.readline()
		
		p.stdout.close()
		stopDaemon(self.els_pid_file)
		with open(self.els_status_file, 'wb+') as f: f.write("False")
	
	def startCronJobs(self):
		self.setCronJob()
	
	def stopCronJobs(self):
		self.setCronJob(enabled=False)
	
	def setCronJob(self, enabled=True):
		try:
			cron = CronTab(tabfile=os.path.join(MONITOR_ROOT, "uv_cron.tab"))
		except IOError as e:
			if DEBUG: print "THERE ARE NO CRONS YET!"
			return

		# enable/disable all the jobs (except for the log one)
		for job in cron:
			if job.comment == "clear_logs": continue
			
			job.enable(enabled)
		
		with settings(warn_only=True):
			local("crontab %s" % os.path.join(MONITOR_ROOT, "uv_cron.tab"))
	
	def initElasticsearch(self):
		if DEBUG: print "INITING ELASTICSEARCH"
		
		from vars import ELASTICSEARCH_MAPPINGS
		index = { "mappings": ELASTICSEARCH_MAPPINGS }

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