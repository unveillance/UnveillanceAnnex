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
			
			if DEBUG: print "NEW ELASICSEARCH MAPPING:\n%s" % lcl[k]
			continue
			
		try:
			lcl[k].update(vars_extras[k])
			if DEBUG: print "updating var: %s" % lcl[k]
		except KeyError as e:
			if DEBUG: print "don't worry, don't have %s" % k
			lcl[k] = vars_extras[k]

QueryBatchRequestStub = namedtuple("QueryBatchRequestStub", "query")
class QueryBatchStub(object):
	def __init__(self, query):
		self.request = QueryBatchRequestStub(query)

QUERY_KEYS = {
	'must' : {
		'match' : ['assets.tags', 'task_path', 'update_file', 'file_name'],
		'filter' : ['mime_type']
	},
	'must_not' : {
		'query_string' : ['mime_type'],
		'filter' : []
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