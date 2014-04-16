from json import loads
from collections import namedtuple

from lib.Core.vars import *
from lib.Worker.vars import *

from conf import DEBUG
lcl = locals()

def inflateVars(path):
	with open(path, 'rb') as VE:
		from json import loads
		try:
			vars_extras = loads(VE.read())
		except Exception as e: return
	
	for k in vars_extras.keys():
		try:
			lcl[k].update(vars_extras[k])
			if DEBUG: print "updating var: %s" % lcl[k]
		except KeyError as e:
			if DEBUG: print "don't worry, don't have %s" % k
			continue

QueryBatchRequestStub = namedtuple("QueryBatchRequestStub", "query")
class QueryBatchStub(object):
	def __init__(self, query):
		self.request = QueryBatchRequestStub(query)

QUERY_KEYS = {
	'must' : {
		'query_string' : ['mime_type', 'assets.tags'],
		'filter' : []
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
				"include_in_root": True
			}
		}
	}
}

try:
	from conf import VARS_EXTRAS
	inflateVars(VARS_EXTRAS)
except ImportError as e:
	if DEBUG: print "no, really, don't worry about vars extras"