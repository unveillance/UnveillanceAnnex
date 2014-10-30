import pandas, re
from datetime import datetime
from fabric.api import settings, local

def forceQuitUnveillance(target=None):
	if target is None:
		target = "unveillance_annex"
	
	with settings(warn_only=True):
		kill_list = local("ps -ef | grep %s.py" % target, capture=True)

		for k in [k.strip() for k in kill_list.splitlines()]:
			if re.match(r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+/bin/sh", k) is not None: continue
			if re.match(r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+grep", k) is not None: continue
			if re.match(r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+.*[Pp]ython\sshutdown.py", k) is not None: continue

			pid = re.findall(re.compile("(?:\d{3,4}|[a-zA-Z0-9_\-\+]{1,8})\s+(\d{4,6}).*%s\.py" % target), k)			
			if len(pid) == 1:
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

def exportFrontendConfig(with_config=None, with_secrets=None):
	import json
	from conf import DEBUG, SERVER_HOST, UUID, ANNEX_DIR, API_PORT
	
	config = {
		'server_host' : SERVER_HOST,
		'server_port' : API_PORT,
		'annex_remote' : ANNEX_DIR,
		'uv_uuid' : UUID,
		'annex_remote_port' : 22,
		'server_use_ssl' : False
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