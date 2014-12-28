import pandas, re
from copy import deepcopy
from datetime import datetime
from time import mktime
from fabric.api import settings, local

from vars import QUERY_DEFAULTS, QUERY_KEYS
from conf import DEBUG

def build_els_query(args, query=None):
	count_only = False
	limit = None
	cast_as = None
	sort = None
	doc_type = "uv_document"
	exclude_fields = True

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
			if DEBUG:
				print "could not find default query for %s" % doc_type.upper()

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

	return (query, { 'doc_type' : doc_type if doc_type != "uv_document" else None,
		'sort' : sort, 
		'count_only' : count_only, 
		'cast_as' : cast_as, 
		'exclude_fields' : exclude_fields })

def forceQuitUnveillance(target=None):
	if target is None:
		target = "unveillance_annex"
	
	with settings(warn_only=True):
		kill_list = local("ps -ef | grep %s.py" % target, capture=True)

		for k in [k.strip() for k in kill_list.splitlines()]:
			if re.match(r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+/bin/sh", k) is not None: continue
			if re.match(r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+grep", k) is not None: continue
			if re.match(r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+.*[Pp]ython\sshutdown.py", k) is not None: continue

			pid = re.findall(re.compile("(?:\d{3,4}|[a-zA-Z0-9_\-\+]{1,8})\s+(\d{2,6}).*%s\.py" % target), k)
			if len(pid) == 1 and len(pid[0]) >= 1:
				try:
					pid = int(pid[0])
				except Exception as e:
					print "ERROR: %s" % e
					continue

				with settings(warn_only=True): local("kill -9 %d" % pid)

def printAsLog(message, as_error=False):
	ts = pandas.DatetimeIndex([datetime.utcnow()])
	
	message = "%s: %s" % (ts.format()[0], message)
	if as_error:
		message = "[ERROR] %s" % message
	
	print message

def exportAnnexConfig(with_config=None):
	import json
	from conf import DEBUG

	config = {}
	required_config = ['uv_log_cron', 'uv_admin_email']
	
	if with_config is not None:
		required_config += with_config if type(with_config) is list else [with_config]

	for c in required_config:
		config[c] = getConfig(c)
	
	for key in [k for k in config.keys() if config[k] is None]:
		del config[key]
	
	print "***********************************************"
	print "THE FOLLOWING LINES MAKE FOR YOUR ANNEX CONFIG\n\n"
	print json.dumps(config)
	print "***********************************************"

	return config

def exportFrontendConfig(with_config=None, with_secrets=None):
	import json
	from conf import DEBUG, SERVER_HOST, UUID, ANNEX_DIR, API_PORT, getConfig, SHA1_INDEX

	server_message_port = None
	try:
		server_message_port = getConfig('server_message_port')
	except:
		pass

	server_user = None
	try:
		server_user = getConfig('server_user')
	except:
		with settings(warn_only=True):
			server_user = local('whoami', capture=True)
	
	config = {
		'server_host' : SERVER_HOST,
		'server_port' : API_PORT,
		'annex_remote' : ANNEX_DIR,
		'uv_uuid' : UUID,
		'annex_remote_port' : 22,
		'server_use_ssl' : False,
		'gdrive_auth_no_ask' : True,
		'server_message_port' : (API_PORT + 1) if server_message_port is None else server_message_port,
		'server_user' : server_user,
		'index.sha1' : SHA1_INDEX
	}
	
	if with_config is not None:
		if type(with_config) is not list:
			with_config = [with_config]
		
		for c in with_config:
			try:
				config[c] = getConfig(c)
			except exception as e:
				if DEBUG: print e
	
	if with_secrets is not None:
		from conf import getSecrets
		if type(with_secrets) is not list:
			with_secrets = [with_secrets]
		
		for s in with_secrets:
			try:
				config[s] = getSecrets(s)
			except exception as e:
				if DEBUG: print e
	
	for key in [k for k in config.keys() if config[k] is None]:
		del config[key]
	
	print "***********************************************"
	print "THE FOLLOWING LINES MAKE FOR YOUR FRONTEND CONFIG\n\n"
	print json.dumps(config)
	print "***********************************************"

	return config
