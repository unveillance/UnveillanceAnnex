import re, sys, os, datetime
from time import sleep, mktime
from copy import deepcopy
from fabric.api import local, settings
from fabric.context_managers import hide

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
		
		if len(args.keys()) in [1, 2]:
			doc_type = None
			try:
				doc_type = args['doc_type']
			except KeyError as e: pass

			if '_id' in args.keys():
				return self.get(_id=args['_id'], els_doc_root=doc_type)
			elif '_ids' in args.keys():
				return self.query({"ids" : {"values" : args['_ids']}}, doc_type=doc_type)

		return self.do_list(request)
		
	def do_list(self, request, query=None):
		count_only = False
		limit = None
		cast_as = None
		sort = None
		doc_type = "uv_document"

		args = parseRequestEntity(request.query)
		if DEBUG: print "\n\nARGS:\n%s\n\n" % args

		try:
			doc_type = args['doc_type']
			del args['doc_type']
		except KeyError as e: pass

		if query is None:
			try:
				query = deepcopy(QUERY_DEFAULTS[doc_type.upper()])
			except Exception as e:
				if DEBUG: print "could not find default query for %s" % doc_type.upper()
				query = deepcopy(QUERY_DEFAULTS['UV_DOCUMENT'])
		
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
							"%s.%s" % (doc_type, a) : args[a]
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
									"%s.%s" % (doc_type, a) : terms
								}
							}
						}
					})
				elif a in QUERY_KEYS[operator]['range']:
					try:
						day = datetime.date.fromtimestamp(args[a]/1000)
					except Exception as e:
						print "TIME ERROR: %s" % e
						return None
						
					if "upper" in args.keys():
						lte = datetime.date.fromtimestamp(args['upper']/1000)
						gte = datetime.date.fromtimestamp(args[a]/1000)
					else:
						lte = datetime.date(day.year, day.month, day.day + 1)
						gte = datetime.date(day.year, day.month, day.day)
					
					query['bool'][operator].append({
						"range" : {
							"%s.%s" % (doc_type, a) : {
								"gte" : format(mktime(gte.timetuple()) * 1000, '0.0f'),
								"lte" : format(mktime(lte.timetuple()) * 1000, '0.0f')
							}
						}
					})
				elif a in QUERY_KEYS[operator]['geo_distance']:
					if "radius" not in args.keys():
						radius = 3
					else:
						radius = args['radius']

					query['bool'][operator].append({
						"geo_distance" : {
							"distance" : "%dmi" % radius,
							"%s.%s" % (doc_type, a) : args[a]
						}
					})
		
		if sort is None:
			sort = [{"%s.date_added" % doc_type: {"order" : "desc"}}]

		return self.query(query, doc_type=doc_type if doc_type != "uv_document" else None,
			sort=sort, count_only=count_only, limit=limit, cast_as=cast_as)
	
	def do_reindex(self, request):
		print "DOING REINDEX"
		
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
				
			inflate.update({
				'task_path' : MIME_TYPE_TASKS[mime_type][0],
				'task_queue' : MIME_TYPE_TASKS[mime_type]
			})
			
		else:
			inflate.update({
				'task_path' :  query['task_path'],
				'no_continue' : True 
			})
		
		uv_task = UnveillanceTask(inflate=inflate)
		uv_task.run()
		return True
	
	def runTask(self, handler):
		try:
			args = parseRequestEntity(handler.request.body)
		except AttributeError as e:
			if DEBUG: print "No body?\n%s" % e
			return None
		
		uv_task = None
		if len(args.keys()) == 1 and '_id' in args.keys():
			uv_task = UnveillanceTask(_id=args['_id'])
		else:
			# TODO: XXX: IF REFERER IS LOCALHOST ONLY (and other auth TBD)!
			if 'task_path' in args.keys():
				args['queue'] = UUID
				uv_task = UnveillanceTask(args)
		
		if uv_task is None: return None
		
		uv_task.run()
		return uv_task.emit()
	
	def fileExistsInAnnex(self, file_path, auto_add=True):
		if file_path == ".gitignore" :
			# WHO IS TRYING TO DO THIS????!
			print "SOMEONE TRIED .gitignore"
			return False
			
		old_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		with settings(hide('everything'), warn_only=True):
			find_cmd = local("git-annex find %s" % file_path, capture=True)				
			if find_cmd == "":
				find_cmd = local("git-annex status %s" % file_path, capture=True)
			
			if find_cmd != "":
				find_cmd = file_path
				local("git-annex add %s" % file_path)			
		
		for line in find_cmd.splitlines():
			if line == file_path:				
				if auto_add:
					web_match_found = False
					m_path = re.compile("\s*web: http\://%s:%d/files/%s" % 
						(HOST, API_PORT, file_path))
				
					with settings(hide('everything'), warn_only=True):
						w_match = local("git-annex whereis %s" % file_path, capture=True)
							
					for w_line in w_match.splitlines():
						# if this file has not already been added to web remote, add it
						if re.match(m_path, w_line) is not None:
							web_match_found = True
							break
								
					if not web_match_found:
						add_cmd = "git-annex addurl --file %s http://%s:%d/files/%s --relaxed" % (file_path, HOST, API_PORT, file_path)
						
						with settings(hide('everything'), warn_only=True):
							add_url = local(add_cmd, capture=True)
							if DEBUG: print "\nFILE'S URL ADDED: %s" % add_url
							# TODO: error handling
							
				os.chdir(old_dir)
				return True
		
		os.chdir(old_dir)
		return False
		
	def syncAnnex(self, file_name, reindex=False):
		uv_tasks = []
		
		create_rx = r'(?:(?!\.data/.*))([a-zA-Z0-9_\-\./]+)'
		task_update_rx = r'(.data/[a-zA-Z0-0]{32}/.*)'

		if reindex or not self.fileExistsInAnnex(file_name, auto_add=False):
			create = re.findall(create_rx, file_name)
			if len(create) == 1:
				# init new file. here it starts.
				if DEBUG: print "INIT NEW FILE: %s" % create[0]
				
				uv_tasks.append(UnveillanceTask(inflate={
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
						uv_tasks.append(UnveillanceTask(inflate={
							'task_path' : matching_task['on_update'],
							'file_name' : task_update[0],
							'doc_id' : matching_task['doc_id'],
							'queue' : UUID
						}))
					except KeyError as e:
						print e
		
		if len(uv_tasks) > 0:
			for uv_task in uv_tasks: uv_task.run()
