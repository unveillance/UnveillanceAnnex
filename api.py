import re, sys, os
from subprocess import Popen, PIPE
from multiprocessing import Process
from time import sleep

from Models.uv_elasticsearch import UnveillanceElasticsearch
from Models.uv_worker import UnveillanceWorker
from lib.Core.Utils.funcs import parseRequestEntity
from lib.Worker.Models.uv_task import UnveillanceTask

from conf import API_PORT, HOST, ANNEX_DIR, MONITOR_ROOT, UUID, DEBUG
from vars import QUERY_KEYS

class UnveillanceAPI(UnveillanceWorker, UnveillanceElasticsearch):
	def __init__(self):
		if DEBUG: print "API started..."
		
		UnveillanceElasticsearch.__init__(self)
		sleep(1)
		UnveillanceWorker.__init__(self)
	
	def do_cluster(self, request):
		"""
			request must be inflated with 
			must !missing asset.tags.file_metadata/key_words/topics, etc.
		"""
		query = {}
		args = parseRequestEntity(request.query)
		if len(args.keys()) > 0:
			if DEBUG:
				print "ALSO SOME MORE PARAMETERS..."
				print args
				
		list = self.do_list((request={'query' : query }, ))
		if list is None: return None
		
		"""
			for whatever the cluster document is,
			generate cluster of those
		"""
		
		return None
	
	def do_list(self, request):		
		count_only = False
		limit = None
		
		query = {
			"bool": {
				"must" : [
					{"query_string" : {
						"default_field" : "uv_document.uv_doc_type",
						"query" : "UV_DOCUMENT" 
					}}
				],
				"must_not" : [
					{ "constant_score" : {"filter" : {
						"missing" : {"field": "uv_document.mime_type"}
					}}}
				]
			}
		}

		args = parseRequestEntity(request.query)
		if len(args.keys()) > 0:
			if DEBUG:
				print "ALSO SOME MORE PARAMETERS..."
				print args

			try:
				count_only = args['count']
				del args['count']
			except KeyError as e: pass
			
			try:
				limit = args['limit']
				del args['limit']
			except KeyError as e: pass
			
			operator = 'must'
			try:
				operator = args['operator']
				del args['operator']
			except KeyError as e: pass
			
			for a in args.keys():
				if a in QUERY_KEYS[operator]['query_string']:
					query['bool'][operator].append({
						"query_string": {
							"default_field" : "uv_document.%s" % a,
							"query" : args[a]
						}
					})

		return self.query(query, count_only=count_only, limit=limit)
	
	def do_document(self, request):
		query = parseRequestEntity(request.query)
		if query is None: return None
		if '_id' not in query.keys(): return None
		
		return self.get(_id=query['_id'])
		
	def do_reindex(self, request):
		query = parseRequestEntity(request.query)
		if query is None: return None
		if '_id' not in query.keys(): return None
		
		document = self.get(_id=query['_id'])
		if document is None: return None
				
		from vars import MIME_TYPE_TASKS
		print MIME_TYPE_TASKS
		
		task = UnveillanceTask(inflate={
			'task_path' : MIME_TYPE_TASKS[document['mime_type']][0],
			'doc_id' : document['_id'],
			'queue' : UUID
		})
		
		task.run()
		return True
	
	def fileExistsInAnnex(self, file_path, auto_add=True):
		if file_path == ".gitignore" :
			# WHO IS TRYING TO DO THIS????!
			return False
			
		old_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		cmd0 = ['git', 'annex', 'find', file_path]			
		p0 = Popen(cmd0, stdout=PIPE, close_fds=True)
		data0 = p0.stdout.readline()

		while data0:
			if DEBUG: print data0
			if data0.strip() == file_path:
				if auto_add:
					web_match_found = False
					m_path = re.compile("\s*web: http\://%s:%d/files/%s" % 
						(HOST, API_PORT, file_path))
					cmd1 = ['git', 'annex', 'whereis', file_path]
					p1 = Popen(cmd1, stdout=PIPE, close_fds=True)
					data1 = p1.stdout.readline()
				
					# if this file has not already been added to web remote, add it
					while data1:
						if re.match(m_path, data1) is not None:
							web_match_found = True
							p1.stdout.close()
							break
				
						data1 = p1.stdout.readline()
					
					p1.stdout.close()
				
					if not web_match_found:
						cmd2 = ['git', 'annex', 'addurl', '--file' , file_path,
							'http://%s:%d/files/%s' % (HOST, API_PORT, file_path),
							'--relaxed']
						p2 = Popen(cmd2, stdout=PIPE, close_fds=True)
						data2 = p2.stdout.readline()
						while data2:
							print data2.strip()
							# TODO: handle error
							data2 = p2.stdout.readline()
						p2.stdout.close()
				
				p0.stdout.close()
				os.chdir(old_dir)
				return True
		
			data0 = p0.stdout.readline()
	
		p0.stdout.close()
		os.chdir(old_dir)
		return False
		
	def syncAnnex(self):
		create_rx = r'\s*create mode (?:\d+) (?:(?!\.data/.*))([a-zA-Z0-9_\-\./]+)'
		cmd = ['git', 'annex', 'sync']
		
		old_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		p = Popen(cmd, stdout=PIPE, close_fds=True)
		data = p.stdout.readline()
		
		tasks = []

		while data:
			print data.strip()
			create = re.findall(create_rx, data.strip())
			if len(create) == 1:
				# init new file. here it starts.
				if DEBUG: print "INIT NEW FILE: %s" % create[0]
				
				tasks.append(UnveillanceTask(inflate={
					'task_path' : "Documents.evaluate_document.evaluateDocument",
					'file_name' : create[0],
					'queue' : UUID
				}))
				
			data = p.stdout.readline()
		p.stdout.close()
		
		os.chdir(old_dir)
		
		if len(tasks) > 0:
			for task in tasks: task.run()