import os, json, re, requests, urllib
from subprocess import Popen, PIPE
from crontab import CronTab
from sys import argv
from time import sleep
from fabric.api import local, settings

from lib.Core.Utils.funcs import stopDaemon, startDaemon
from Utils.funcs import printAsLog
from conf import MONITOR_ROOT, CONF_ROOT, ELS_ROOT, DEBUG
from vars import ELASTICSEARCH_SOURCE_EXCLUDES

class UnveillanceElasticsearchHandler(object):
	def __init__(self):
		if DEBUG: print "elasticsearch handler inited"
		
	def get(self, _id, els_doc_root=None, parent=None):
		if DEBUG: print "getting thing"

		res = self.sendELSRequest(endpoint=self.buildEndpoint(_id, els_doc_root, parent))

		try:
			if res['found']: return res['_source']
		except KeyError as e: 
			if DEBUG: print "ERROR ON GET: %s" % e
			pass
		
		return None

	def buildDocumentsFromScroll(self, _scroll_id, with_documents=None, limit=None, exclude_fields=False, cast_as=None):
		if with_documents is None: with_documents = []
		
		if type(limit) is int and len(with_documents) >= limit:
			return with_documents

		scroll = self.iterateOverScroll(_scroll_id, exclude_fields=exclude_fields, cast_as=cast_as)
		
		if scroll is not None and not scroll['scroll_end']:
			return self.buildDocumentsFromScroll(scroll['_scroll_id'],
				with_documents=(with_documents + scroll['documents']), limit=limit)

		return with_documents

	def iterateOverScroll(self, _scroll_id, exclude_fields=True, cast_as=None):		
		res = self.sendELSRequest(endpoint="_search/scroll?scroll=600s&scroll_id=%s" % _scroll_id, to_root=True)		
		next_scroll_id = res['_scroll_id']

		documents = [d['_source'] for d in res['hits']['hits']]

		if cast_as is not None:
			casts = [d[cast_as] for d in documents]
			query = {
				'query' : { 'ids' : { 'values' : casts }},
				'sort' : [{ 'uv_document.date_added' : { 'order' : 'desc' }}]
			}
			
			if DEBUG: print "\nCASTING TO %s:\n%s\n" % (cast_as, query)
			res = self.sendELSRequest(endpoint=self.buildEndpoint("_search", None, None), 
				method="post", data=query)
			
			documents = [d['_source'] for d in res['hits']['hits']]

		if exclude_fields and len(ELASTICSEARCH_SOURCE_EXCLUDES) > 0:
			for ex in ELASTICSEARCH_SOURCE_EXCLUDES:
				map(lambda d: d.pop(ex, None), documents)

		return {
			"documents" : documents,
			"_scroll_id" : next_scroll_id,
			"scroll_end" : True if str(next_scroll_id) == str(_scroll_id) else False
		}

	def getScroll(self, query, build=True, doc_type=None, sort=None, exclude_fields=False, cast_as=None):
		if sort is None: sort = [{"%s.date_added" % doc_type : {"order" : "desc"}}]
		else:
			if type(sort) is not list: sort = [sort]

		if doc_type is None: doc_type = "uv_document"

		query = {
			'query' : json.loads(urllib.unquote(json.dumps(query))),
			'sort' : sort
		}

		if DEBUG: 
			print "OH A QUERY"
			print json.dumps(query)

		endpoint = "%s?search_type=scan&scroll=600s" % self.buildEndpoint("_search", doc_type, None)
		res = self.sendELSRequest(endpoint=endpoint, data=query)

		try:
			if res['hits']['total'] == 0:
				if DEBUG: print "NO HITS FOUND."
				return None

			res = self.iterateOverScroll(res['_scroll_id'],
				exclude_fields=exclude_fields, cast_as=cast_as)

			res['count'] = len(res['documents'])
			return res

		except Exception as e:
			if DEBUG: print "BAD SCROLL SEARCH: %s" % e
		
		return None

	def query(self, query, limit=None, exclude_fields=False, doc_type=None, count_only=False, 
		sort=None, cast_as=None):
		
		if doc_type is None: doc_type = "uv_document"

		if sort is None: sort = [{"%s.date_added" % doc_type : {"order" : "desc"}}]
		else:
			if type(sort) is not list: sort = [sort]

		res = self.getScroll(query, doc_type=doc_type, exclude_fields=exclude_fields,
			sort=sort, cast_as=cast_as)
		
		if res is None: return None
		if count_only: return res['count']

		res['documents'] = self.buildDocumentsFromScroll(res['_scroll_id'], cast_as=cast_as,
			with_documents=res['documents'], limit=limit, exclude_fields=exclude_fields)

		if "_scroll_id" in res.keys(): del res['_scroll_id']
		return res
	
	def updateFields(self, _id, args, els_doc_root=None, parent=None):
		res = self.sendELSRequest(method="post", data={ "doc" : args },
			endpoint="/".join([self.buildEndpoint(_id, els_doc_root, None), "_update"]))
		
		if DEBUG: print res
		
		try: 
			if 'error' not in res.keys(): return True
		except Exception as e:
			if DEBUG: print "ERROR ON UPDATE:\n%s" % e
			pass
		
		return False
	
	def update(self, _id, args, els_doc_root=None, parent=None):
		if DEBUG: print "updating thing"
		
		res = self.sendELSRequest(endpoint=self.buildEndpoint(_id, els_doc_root, parent), 
			data=args, method="put")

		try: return res['ok']
		except KeyError as e: pass
		
		return False
	
	def create(self, _id, args, els_doc_root=None, parent=None):
		if DEBUG: print "creating thing"

		if hasattr(self, "els_doc_root"):
			els_doc_root = self.els_doc_root
			if DEBUG: print "Creating thing on another doc_root:\n%s" % self.emit().keys()

			if hasattr(self, "media_id"): parent = self.media_id
			else:
				if DEBUG: print "no parent though..."

		return self.update(_id, args, els_doc_root=els_doc_root, parent=parent)
		
	def delete(self, _id, els_doc_root=None, parent=None):
		if DEBUG: print "deleting thing"
		
		res = self.sendELSRequest(endpoint=self.buildEndpoint(_id, els_doc_root, parent),
			method="delete")
		
		if DEBUG: print res
		
		try: return res['ok']
		except KeyError as e: pass
		
		return False

	def buildEndpoint(self, _id, els_doc_root, parent):
		return "%s%s" % ("/".join(["uv_document" if els_doc_root is None else els_doc_root, _id]),
			"" if parent is None else "?parent=%s" % parent)

	def sendELSRequest(self, data=None, endpoint=None, to_root=False, method="get"):
		url = "http://localhost:9200/"

		if not to_root: url += "unveillance/"
		if endpoint is not None: url += endpoint
		if data is not None: data = json.dumps(data)

		if DEBUG: print "****\nSENDING ELS REQUEST TO %s\n****" % url
		
		try:
			if method == "get":
				r = requests.get(url, data=data)
			elif method == "post":
				r = requests.post(url, data=data)
			elif method == "put":
				r = requests.put(url, data=data)
			elif method == "delete":
				r = requests.delete(url, data=data)
		except Exception as e:
			if DEBUG: print "ERROR ACCESSING ELASTICSEARCH: %s" % e
			return None
		
		if hasattr(r, "content"):
			try:
				return json.loads(r.content)
			except Exception as e:
				print "BIG ERROR: %s" % e
				print r.content
		elif hasattr(r, "text"):
			try:
				return json.loads(r.text)
			except Exception as e:
				print "BIG ERROR: %s" % e
		
		return None

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

		#if self.first_use:
		startDaemon(self.els_log_file, self.els_pid_file)
		self.startCronJobs()

		try:
			with open(os.path.join(CONF_ROOT, "initial_tasks.json"), 'rb') as IT:
				from lib.Worker.Models.uv_task import UnveillanceTask
				for i_task in json.loads(IT.read()):
					task = UnveillanceTask(inflate=i_task)

					try:
						task.run()
					except Exception as e:
						if DEBUG:
							print "TASK ERROR: %s" % e

		except Exception as e:
			if DEBUG:
				print "No initial tasks...\n%s" % e
			
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
			if enabled:
				local("crontab %s" % os.path.join(MONITOR_ROOT, "uv_cron.tab"))
			else:
				local("crontab -r")
	
	def initElasticsearch(self):
		if DEBUG: print "INITING ELASTICSEARCH"
		
		from vars import ELASTICSEARCH_MAPPINGS
		index = { "mappings": ELASTICSEARCH_MAPPINGS }

		try:
			res = self.sendELSRequest(method="delete")
			
			if DEBUG:
				print "DELETED OLD MAPPING:"
				print res
		except Exception as e: 
			if DEBUG: print e
			printAsLog(e, as_error=True)
				
		try:
			res = self.sendELSRequest(data=index, method="put")
			if DEBUG:
				print "INITIALIZED NEW MAPPING:"
				print res
			
			if not res['acknowledged']: return False
					
		except Exception as e:
			printAsLog(e, as_error=True)
			return False