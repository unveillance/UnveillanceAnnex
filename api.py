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

from conf import API_PORT, HOST, ANNEX_DIR, MONITOR_ROOT, UUID, DEBUG, SHA1_INDEX
from vars import QUERY_KEYS, QUERY_DEFAULTS, QueryBatchRequestStub

class UnveillanceAPI(UnveillanceWorker, UnveillanceElasticsearch):
	def __init__(self):
		if DEBUG: print "API started..."
		
		UnveillanceElasticsearch.__init__(self)
		sleep(1)
		UnveillanceWorker.__init__(self)
		sleep(2)

	def do_cluster(self, request):
		"""
			request must be inflated with 
			must !missing asset.tags.file_metadata/key_words/topics, etc.
		"""
		args = parseRequestEntity(request.query)

		if len(args.keys()) == 0: return None
		for required in ['task_path', 'documents']:
			if required not in args.keys(): return None
			
		cluster = UnveillanceCluster(inflate=args)
		
		try:
			return cluster.communicate()
		
		except Exception as e:
			if DEBUG:
				print e
			return None

	def do_tasks(self, request):
		args = parseRequestEntity(request.query)
		
		if len(args.keys()) == 1 and '_id' in args.keys():
			return self.get(_id=args['_id'])
		
		return self.do_list(request, query=deepcopy(QUERY_DEFAULTS['UV_TASK']))
	
	def do_documents(self, request):
		args = parseRequestEntity(request.query)
		
		if len(args.keys()) in [1, 2, 3]:
			doc_type = None
			try:
				doc_type = args['doc_type']
			except KeyError as e: pass

			media_id = None
			try:
				media_id = args['media_id']
				del args['media_id']
			except KeyError as e: pass

			if '_id' in args.keys():
				return self.get(_id=args['_id'], els_doc_root=doc_type, parent=media_id)
			elif '_ids' in args.keys():
				return self.query({"ids" : {"values" : args['_ids']}}, doc_type=doc_type, exclude_fields=False)

		return self.do_list(request)
		
	def do_list(self, request, query=None):
		count_only = False
		limit = None
		cast_as = None
		sort = None
		doc_type = "uv_document"
		exclude_fields = True

		args = parseRequestEntity(request.query)
		if DEBUG: print "\n\nARGS:\n%s\n\n" % args

		try:
			doc_type = args['doc_type']
			del args['doc_type']
		except KeyError as e: pass

		try:
			exclude_fields = not args['get_all']
			print exclude_fields
			del args['get_all']
		except KeyError as e: pass

		try:
			sort = args['sort']
			del args['sort']
		except KeyError as e: pass

		if query is None:
			try:
				query = deepcopy(QUERY_DEFAULTS[doc_type.upper()])
			except Exception as e:
				if DEBUG: print "could not find default query for %s" % doc_type.upper()
				query = deepcopy(QUERY_DEFAULTS['MATCH_ALL'])
		
		if len(args.keys()) > 0:
			# pull out variables that don't go in search
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

		if len(args.keys()) > 0:
			# extend out top-level query
			musts = []

			for a in args.keys():
				must = None
				if a in QUERY_KEYS['match']:
					must = {
						"match" : { "%s.%s" % (doc_type, a) : args[a] }
					}

				elif a in QUERY_KEYS['filter_terms']:
					must = {
						"constant_score" : {
							"filter" : {
								"terms" : {
									"%s.%s" % (doc_type, a) : args[a] if type(args[a]) is list else [args[a]]
								}
							}
						}
					}

				elif a in QUERY_KEYS['filter_ids']:
					must = {
						"ids" : {
							"type" : doc_type,
							"values" : args[a] if type(args[a]) is list else [args[a]]
						}
					}

					musts = [must]
					del args[a]					
					break

				if must is not None:
					del args[a]
					musts.append(must)

			if len(musts) > 0:
				if 'match_all' in query.keys():
					del query['match_all']

				if musts[0].keys()[0] == "ids":
					query = musts[0]
				else:
					if 'bool' not in query.keys():
						query['bool'] = { "must" : [] }

					if 'must' not in query['bool'].keys():
						query['bool']['must'] = []

					for must in musts: query['bool']['must'].append(must)

		if len(args.keys()) > 0:
			# this becomes a filtered query
			query = {
				"filtered" : {
					"query" : query,
					"filter" : {}
				}
			}
			
			filters = []
			for a in args.keys():
				filter = None

				if 'term' in QUERY_KEYS and a in QUERY_KEYS['term']:
					filter = { "term": { "%s.%s" % (doc_type, a) : args[a] }}

				elif 'range' in QUERY_KEYS and a in QUERY_KEYS['range']:
					try:
						day = datetime.date.fromtimestamp(args[a]/1000)
					except Exception as e:
						print "TIME ERROR: %s" % e
						continue
						
					if "upper" in args.keys():
						lte = datetime.date.fromtimestamp(args['upper']/1000)
						gte = datetime.date.fromtimestamp(args[a]/1000)
					else:
						lte = datetime.date(day.year, day.month, day.day + 1)
						gte = datetime.date(day.year, day.month, day.day)
					
					filter = {
						"range" : {
							"%s.%s" % (doc_type, a) : {
								"gte" : format(mktime(gte.timetuple()) * 1000, '0.0f'),
								"lte" : format(mktime(lte.timetuple()) * 1000, '0.0f')
							}
						}
					}

				elif 'geo_distance' in QUERY_KEYS and a in QUERY_KEYS['geo_distance']:
					if "radius" not in args.keys():
						radius = 3
					else:
						radius = args['radius']

					filter = {
						"geo_distance" : {
							"distance" : "%dmi" % radius,
							"%s.%s" % (doc_type, a) : args[a]
						}
					}

				if filter is not None:
					filters.append(filter)

			if len(filters) > 1:
				query['filtered']['filter']['and'] = filters
			else:
				if len(filters) == 1:
					try:
						query['filtered']['filter'] = filters[0]
					except Exception as e:
						print "COULD NOT BUILD QUERY: %s" % e
						return None
		
		return self.query(query, doc_type=doc_type if doc_type != "uv_document" else None,
			sort=sort, count_only=count_only, cast_as=cast_as, exclude_fields=exclude_fields)
	
	def do_reindex(self, request):
		print "DOING REINDEX"
		
		query = parseRequestEntity(request.query)
		if query is None: return None
		if '_id' not in query.keys(): return None
		
		document = self.get(_id=query['_id'])
		if document is None: return None
		
		inflate={
			'doc_id' : document['_id'],
			'queue' : UUID
		}
		
		if 'task_path' not in query.keys() and 'task_queue' not in query.keys():
			inflate.update({
				'task_path' : "Documents.evaluate_document.evaluateDocument"
			})
			
		else:
			if 'task_queue' in query.keys():
				inflate.update({
					'task_path' : query['task_queue'][0],
					'task_queue' : query['task_queue']
				})
			else:
				inflate.update({
					'task_path' :  query['task_path'],
					'no_continue' : True 
				})

		if 'task_extras' in query.keys():
			inflate.update(query['task_extras'])
			inflate['persist_keys'] = query['task_extras'].keys()

		if DEBUG:
			print "TASK TO GO THROUGH REINDEXER:"
			print inflate
		
		uv_task = UnveillanceTask(inflate=inflate)
		uv_task.run()
		
		return uv_task.emit()
	
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
				uv_task = UnveillanceTask(inflate=args)
		
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
		task_update_rx = re.compile('(.data/[a-zA-Z0-0]{%d}/.*)' % 32 if not SHA1_INDEX else 40)

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
			
			'''
			task_update = re.findall(task_update_rx, file_name)
			if len(task_update) == 1:
				if DEBUG:
					print "UPDATING TASK BY PATH %s" % task_update[0]
				
				matching_tasks = self.do_tasks(QueryBatchRequestStub(
					"update_file=%s" % task_update[0]))
				
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
			'''
		if len(uv_tasks) > 0:
			for uv_task in uv_tasks: uv_task.run()