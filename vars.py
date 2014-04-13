from lib.Core.vars import *
from lib.Worker.vars import *

QUERY_KEYS = {
	'must' : {
		'query_string' : ['mime_type'],
		'filter' : []
	},
	'must_not' : {
		'query_string' : ['mime_type'],
		'filter' : []
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