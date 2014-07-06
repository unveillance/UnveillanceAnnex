from json import loads
from collections import namedtuple

from lib.Core.vars import *
from lib.Worker.vars import *

from conf import DEBUG
lcl = locals()

def inflateVars(path):
	print "INFLATING EXTRA VARS..."
	with open(path, 'rb') as VE:
		from json import loads
		try:
			vars_extras = loads(VE.read())
		except Exception as e: 
			if DEBUG: print "error inflating vars: %s" % e
			return
	
	for k in vars_extras.keys():
		if k == "ELASTICSEARCH_MAPPINGS":
			for key in vars_extras[k].keys():
				if key in lcl[k]['uv_document']['properties'].keys():
					del vars_extras[k][key]
					# no overwriting our default elasticsearch mappings!
			
			if len(vars_extras[k].keys()) == 0: continue
			
			lcl[k]['uv_document']['properties'].update(vars_extras[k])
			continue
		elif k == "QUERY_KEYS":			
			for operator in vars_extras[k].keys():
				if DEBUG: print "Operator: %s" % operator
				
				if operator in QUERY_KEYS.keys():
					for query_type in vars_extras[k][operator].keys():
						if DEBUG: print "query type: %s" % query_type
						qts = vars_extras[k][operator][query_type]
						
						if type(qts) is not list: qts = [qts]
						if DEBUG: print qts
						
						if query_type in QUERY_KEYS[operator].keys():
							if DEBUG: print "UPDATING %s" % query_type
							QUERY_KEYS[operator][query_type].extend(qts)
						else:
							QUERY_KEYS[operator][query_type] = qts
				else:
					QUERY_KEYS.update(vars_extras[k][operator])
			
			if DEBUG:
				print "\n\nNEW QUERY KEYS:\n%s" % QUERY_KEYS
				print "\n\n"
			continue
			
		try:
			lcl[k].update(vars_extras[k])
			if DEBUG: print "\nupdating %s: %s\n" % (k, lcl[k])
		except KeyError as e:
			if DEBUG: print "\ndon't worry, don't have %s" % k
			lcl[k] = vars_extras[k]

QueryBatchRequestStub = namedtuple("QueryBatchRequestStub", "query")
class QueryBatchStub(object):
	def __init__(self, query):
		self.request = QueryBatchRequestStub(query)

QUERY_KEYS = {
	'must' : {
		'match' : ['assets.tags', 'task_path', 'update_file', 'file_name'],
		'filter' : ['mime_type'],
		'range' : ['date_added'],
		'geo_distance' : [],
		'query_string' : []
	},
	'must_not' : {
		'query_string' : ['mime_type'],
		'filter' : [],
		'match' : [],
		'range' : [],
		'geo_distance' : []
	}
}

QUERY_DEFAULTS = {
	'UV_DOCUMENT' : {
		"bool": {
			"must" : [
				{"match" : {
					"uv_document.uv_doc_type" : "UV_DOCUMENT" 
				}}
			],
			"must_not" : [
				{ "constant_score" : {"filter" : {
					"missing" : {"field": "uv_document.mime_type"}
				}}}
			]
		}
	},
	'UV_TASK' : {
		"bool": {
			"must" : [
				{"query_string" : {
					"default_field" : "uv_document.uv_doc_type",
					"query" : "UV_TASK" 
				}}
			]
		}
	}
}

ELASTICSEARCH_MAPPINGS = {
	"uv_document" : {
		"properties": {
			"uv_type": {
				"type" : "string",
				"store" : True
			},
			"assets": {
				"type" : "nested",
				"include_in_parent": True,
				"include_in_root": True,
				"properties" : {
					"file_name" : {
						"type" : "string",
						"index" : "not_analyzed"
					}
				}
			},
			"file_name" : {
				"type" : "string",
				"index" : "not_analyzed",
				"store" : True
			},
			"mime_type": {
				"type" : "string",
				"index" : "not_analyzed",
				"store" : True
			},
			"farm": {
				"type" : "string",
				"index" : "not_analyzed",
				"store" : True
			},
			"uv_doc_type": {
				"type" : "string",
				"index" : "not_analyzed",
				"store" : True
			}
		}
	}
}

try:
	from conf import VARS_EXTRAS
	inflateVars(VARS_EXTRAS)
except ImportError as e:
	if DEBUG: print "no, really, don't worry about vars extras"