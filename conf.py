import os, yaml, json
from collections import namedtuple

SERVER_HOST = os.getenv('UV_SERVER_HOST')
UUID = os.getenv('UV_UUID')
HOST = "localhost"
ELS_PORT = 9200

this_dir = os.path.abspath(os.path.join(__file__, os.pardir))
CONF_ROOT = os.path.join(this_dir, "conf")

with open(os.path.join(CONF_ROOT, "annex.settings.yaml"), 'rb') as C:
	config = yaml.load(C.read())
	API_PORT = config['api.port']
	TASK_CHANNEL_PORT = API_PORT + 1
	NUM_PROCESSES = config['api.num_processes']
	DEBUG = config['flags.debug']

	SHA1_INDEX = False
	try:
		SHA1_INDEX = config['index.sha1']
	except KeyError as e:
		pass

with open(os.path.join(CONF_ROOT, "annex.config.yaml"), 'rb') as C:
	config = yaml.load(C.read())
	ANNEX_DIR = config['annex_dir']
	BASE_DIR = config['base_dir']
	MONITOR_ROOT = os.path.join(BASE_DIR, ".monitor")
	ELS_ROOT = os.path.join(BASE_DIR, config['els_root'])
	SSH_ROOT = config['ssh_root']
	
	try:
		DOC_SALT = config['document_salt']
	except KeyError as e:
		if DEBUG: print "no doc salt yet..."
	
	try:
		VARS_EXTRAS = config['vars_extras']
	except KeyError as e:
		if DEBUG: print "DON'T WORRY: no variable extras..."

	MASTER_GIST = None
	try:
		MASTER_GIST = config['master_gist']
	except KeyError as e:
		if DEBUG:
			print "No Master Gist, this is okay..."

def getConfig(key):
	with open(os.path.join(CONF_ROOT, "annex.config.yaml"), 'rb') as C:
		config = yaml.load(C.read())
		try:
			return config[key]
		except Exception as e: raise e

def getSecrets(key):
	try:
		with open(os.path.join(CONF_ROOT, "unveillance.secrets.json"), 'rb') as C:
			config = json.loads(C.read())
		
			try:
				return config[key]
			except Exception as e: raise e
	except IOError as e: raise e