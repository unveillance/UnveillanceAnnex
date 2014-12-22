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

		elif k == "ELASTICSEARCH_SOURCE_EXCLUDES":
			for exclude in vars_extras[k]:
				ELASTICSEARCH_SOURCE_EXCLUDES.append(exclude)

			print "NEW ELASTICSEARCH_SOURCE_EXCLUDES:"
			print ELASTICSEARCH_SOURCE_EXCLUDES
			continue

		elif k == "TASK_PERSIST_KEYS":
			for exclude in vars_extras[k]:
				TASK_PERSIST_KEYS.append(exclude)
				
			print "NEW TASK_PERSIST_KEYS"
			print TASK_PERSIST_KEYS
			continue

		elif k == "QUERY_KEYS":
			for key in vars_extras[k].keys():
				qts = vars_extras[k][key]
				
				if type(qts) is not list: qts = [qts]
				if DEBUG: print qts

				if key in QUERY_KEYS.keys():
					if DEBUG: print "UPDATING %s" % key
					QUERY_KEYS[key]= list(set(QUERY_KEYS[key] + qts))
				
				else:
					QUERY_KEYS[key] = qts
			print vars_extras[k]
			continue

		elif k == "CUSTOM_QUERIES" :
			for key in vars_extras[k].keys():
				if key in lcl['CUSTOM_QUERIES'].keys():
					del vars_extras[k][key]

			if len(vars_extras[k].keys()) == 0: continue

			lcl['CUSTOM_QUERIES'].update(vars_extras[k])
		elif k == "QUERY_DEFAULTS":
			for key in vars_extras[k].keys():
				if key in lcl['QUERY_DEFAULTS'].keys():
					del vars_extras[k][key]

			if len(vars_extras[k].keys()) == 0: continue

			lcl['QUERY_DEFAULTS'].update(vars_extras[k])

		elif k == "ELASTICSEARCH_MAPPING_STUBS":
			for key in vars_extras[k].keys():
				if key in lcl['ELASTICSEARCH_MAPPINGS'].keys():
					del vars_extras[k][key]
					continue
					# no overwriting, again!
				
			if len(vars_extras[k].keys()) == 0: continue

			lcl['ELASTICSEARCH_MAPPINGS'].update(vars_extras[k])
			continue
			
		try:
			lcl[k].update(vars_extras[k])
			#if DEBUG: print "\nupdating %s: %s\n" % (k, lcl[k])
		except KeyError as e:
			#if DEBUG: print "\ndon't worry, don't have %s" % k
			lcl[k] = vars_extras[k]

QueryBatchRequestStub = namedtuple("QueryBatchRequestStub", "query")
class QueryBatchStub(object):
	def __init__(self, query):
		self.request = QueryBatchRequestStub(query)

GIT_ANNEX_METADATA = ['uv_file_alias', 'importer_source', 'imported_by', 'uv_local_only']

TASK_PERSIST_KEYS = ["doc_id", "queue", "task_queue", "log_file", "recurring"]

QUERY_KEYS = {
	'match' : ['assets.tags', 'task_path', 'update_file', 'file_name', 'media_id'],
	'range' : ['date_added'],
	'filter_terms' : ['mime_type', 'searchable_text', 'file_alias'],
	'filter_ids' : ['in_pool']
}

QUERY_DEFAULTS = {
	'MATCH_ALL' : {
		"match_all" : {}
	},
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

CUSTOM_QUERIES = {
	"GET_ALL_WITH_ATTACHMENTS" : {
		"bool" : {
			"must_not" : [
				{
					"constant_score" : {
						"filter" : {
							"missing" : {
								"field" : "uv_document.documents"
							}
						}
					}
				}
			]
		}
	},
	"GET_BY_FILE_NAME" : {
		"bool" : {
			"must" : [
				{
					"match" : {
						"uv_document.file_name" : "%s"
					}
				}
			]
		}
	}
}

ELASTICSEARCH_SOURCE_EXCLUDES = ["searchable_text"]

ELASTICSEARCH_MAPPINGS = {
	"uv_text_stub" : {
		"_parent" : {
			"type" : "uv_document"
		},
		"properties" : {
			"searchable_text" : {
				"type" : "string"
			}
		}
	},
	"uv_cluster" : {
		"properties" : {
			"uv_task" : {
				"type" : "string",
				"index" : "not_analyzed",
				"store" : True
			}
		}
	},
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
	#if DEBUG: print "no, really, don't worry about vars extras"
	pass