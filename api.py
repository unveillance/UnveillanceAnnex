import re, sys, os
from subprocess import Popen, PIPE
from multiprocessing import Process
from time import sleep
from copy import deepcopy

from Models.uv_elasticsearch import UnveillanceElasticsearch
from Models.uv_worker import UnveillanceWorker
from lib.Core.Utils.funcs import parseRequestEntity
from lib.Worker.Models.uv_task import UnveillanceTask
from lib.Worker.Models.uv_cluster import UnveillanceCluster

from conf import API_PORT, HOST, ANNEX_DIR, MONITOR_ROOT, UUID, DEBUG
from vars import QUERY_KEYS, QUERY_DEFAULTS, QueryBatchRequestStub

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
		args = parseRequestEntity(request.query)
		if len(args.keys()) == 0: return None
		
		if len(args.keys()) == 1 and '_id' in args.keys():
			return self.get(_id=args['_id'])
					
		if 'around' not in args.keys(): return None
		asset_tag = args['around']
		del args['around']
		
		query = "assets.tags=%s" % asset_tag
		
		if '_ids' in args.keys():
			documents = args['_ids'].split(",")	
		else:	
			list = self.do_documents(QueryBatchRequestStub(query))
			if list is None: return None
			
			documents = [d['_id'] for d in list['documents']]
			
		cluster = UnveillanceCluster(inflate={
			'documents' : documents,
			'asset_tag' : asset_tag
		})
		if cluster is None: return None
		
		try:
			return {
				'_id' : cluster._id, 
				'cluster' : cluster.getAssetsByTagName("metadata_fingerprint")[0]
			}
		
		except Exception as e:
			if DEBUG: print e
			return None

	def do_tasks(self, request):
		args = parseRequestEntity(request.query)
		
		if len(args.keys()) == 1 and '_id' in args.keys():
			return self.get(_id=args['_id'])
		
		return self.do_list(request, query=deepcopy(QUERY_DEFAULTS['UV_TASK']))
	
	def do_documents(self, request):
		args = parseRequestEntity(request.query)
		if len(args.keys()) == 1 and '_id' in args.keys():
			return self.get(_id=args['_id'])
		
		return self.do_list(request)
		
	def do_list(self, request, query=None):
		count_only = False
		limit = None
		
		if query is None:
			query = deepcopy(QUERY_DEFAULTS['UV_DOCUMENT'])

		args = parseRequestEntity(request.query)
		if len(args.keys()) > 0:
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
			print "SOMEONE TRIED .gitignore"
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
		task_update_rx = r'\s*create mode (?:\d+) (.data/[a-zA-Z0-0]{32}/.*)'
		
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
			
			task_update = re.findall(task_update_rx, data.strip())
			if len(task_update) == 1:
				if DEBUG: print "UPDATING TASK BY PATH %s" % task_update[0]
				
				matching_tasks = self.do_tasks(QueryBatchRequestStub(
					"update_file=%s" % task_update[0]))
				print matching_tasks
				if matching_tasks is not None:
					matching_task = matching_tasks['documents'][0]			
					try:
						tasks.append(UnveillanceTask(inflate={
							'task_path' : matching_task['on_update'],
							'file_name' : task_update[0],
							'doc_id' : matching_task['doc_id'],
							'queue' : UUID
						}))
					except KeyError as e:
						print e
				
			data = p.stdout.readline()
		p.stdout.close()
		
		os.chdir(old_dir)
		
		if len(tasks) > 0:
			for task in tasks: task.run()