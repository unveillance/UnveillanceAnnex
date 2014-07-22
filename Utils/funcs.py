import pandas
from datetime import datetime

def printAsLog(message, as_error=False):
	ts = pandas.DatetimeIndex([datetime.utcnow()])
	
	message = "%s: %s" % (ts.format()[0], message)
	if as_error:
		message = "[ERROR] %s" % message
	
	print message

def exportFrontendConfig(with_config=None, with_secrets=None):
	import json
	from conf import DEBUG, SERVER_HOST, UUID, ANNEX_DIR, API_PORT
	
	config = {
		'server_host' : SERVER_HOST,
		'server_port' : API_PORT,
		'annex_remote' : ANNEX_DIR,
		'uv_uuid' : UUID
	}
	
	if with_config is not None:
		from conf import getConfig
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
	print json.dumps(config)
	print "***********************************************"