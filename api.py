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
		sleep(5)

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
		cast_as = None
		
		if query is None:
			query = deepcopy(QUERY_DEFAULTS['UV_DOCUMENT'])

		args = parseRequestEntity(request.query)
		if DEBUG: print "\n\nARGS:\n%s\n\n" % args
		
		if len(args.keys()) > 0:
			try:
				count_only = args['count']
				del args['count']
			except KeyError as e: pass
			
			try:
				limit = args['limit']
				del args['limit']
			except KeyError as e: pass
			
			try:
				cast_as = args['cast_as']
				del args['cast_as']
			except KeyError as e: pass
			
			operator = 'must'
			try:
				operator = args['operator']
				del args['operator']
			except KeyError as e: pass
			
			for a in args.keys():
				if a in QUERY_KEYS[operator]['match']:
					query['bool'][operator].append({
						"match": {
							"uv_document.%s" % a : args[a]
						}
					})
				elif a in QUERY_KEYS[operator]['filter']:
					terms = args[a]
					if type(terms) is not list:
						terms = [terms]
					
					query['bool'][operator].append({
						"constant_score" : {
							"filter" : {
								"terms" : {
									"uv_document.%s" % a : terms
								}
							}
						}
					})
		
		return self.query(query, count_only=count_only, limit=limit, cast_as=cast_as)
	
	def runTask(self, handler):
		try:
			args = parseRequestEntity(handler.request.body)
		except AttributeError as e:
			if DEBUG: print "No body?\n%s" % e
			return None
		
		task = None
		if len(args.keys()) == 1 and '_id' in args.keys():
			task = UnveillanceTask(_id=args['_id'])
		else:
			# TODO: XXX: IF REFERER IS LOCALHOST ONLY (and other auth TBD)!
			if 'task_path' in args.keys():
				args['queue'] = UUID
				task = UnveillanceTask(args)
		
		if task is None: return None
		
		task.run()
		return task.emit()
	
	def do_reindex(self, request):
		query = parseRequestEntity(request.query)
		if query is None: return None
		if '_id' not in query.keys(): return None
		
		document = self.get(_id=query['_id'])
		if document is None: return None
				
		from vars import MIME_TYPE_TASKS
		print MIME_TYPE_TASKS
		
		inflate={
			'doc_id' : document['_id'],
			'queue' : UUID
		}
		
		if 'task_path' not in query.keys():
			if 'original_mime_type' in document.keys():
				mime_type = document['original_mime_type']
			else:
				mime_type = document['mime_type']
				
			inflate['task_path'] = MIME_TYPE_TASKS[mime_type][0]
		else:
			inflate.update({
				'task_path' :  query['task_path'],
				'no_continue' : True 
			})
		
		task = UnveillanceTask(inflate=inflate)
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
		if DEBUG: print "SEARCHING FOR FILE IN ANNEX WITH\n%s" % cmd0
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
		
	def syncAnnex(self, file_name):
		tasks = []
		
		create_rx = r'(?:(?!\.data/.*))([a-zA-Z0-9_\-\./]+)'
		task_update_rx = r'(.data/[a-zA-Z0-0]{32}/.*)'

		if not self.fileExistsInAnnex(file_name, auto_add=False):
			create = re.findall(create_rx, file_name)
			if len(create) == 1:
				# init new file. here it starts.
				if DEBUG: print "INIT NEW FILE: %s" % create[0]
				
				tasks.append(UnveillanceTask(inflate={
					'task_path' : "Documents.evaluate_document.evaluateDocument",
					'file_name' : file_name,
					'queue' : UUID
				}))
			
			task_update = re.findall(task_update_rx, file_name)
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
		
		if len(tasks) > 0:
			for task in tasks: task.run()