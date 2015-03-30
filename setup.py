import re, os, json
from crontab import CronTab
from sys import argv, exit
from time import sleep
from fabric.api import local, settings
from fabric.operations import prompt

def locateLibrary(lib_rx):
	base_dir = os.getcwd()
	
	for _, dir, _ in os.walk(os.path.join(base_dir, "lib")):
		print dir
		for d in dir:
			if re.match(lib_rx, d) is not None:
				return os.path.join(base_dir, "lib", d)

		break
	
	return None

def initAnnex(annex_dir, base_dir, python_home):
	os.chdir(annex_dir)
	with settings(warn_only=True):
		local("git init")
		
		if not os.path.exists(".git/hooks"):
			local("mkdir .git/hooks")

	with open(os.path.join(annex_dir, ".git", "hooks", "uv-post-netcat"), 'wb+') as HOOK:
		HOOK.write("cd %s\n%s sync_file.py \"$@\"" % (base_dir, python_home))

	with open(os.path.join(annex_dir, ".git", "hooks", "uv-on-upload-attempted"), 'wb+') as HOOK:
		HOOK.write("cd %s\n%s register_upload_attempt.py $1" % (base_dir, python_home))
		
	with settings(warn_only=True):
		for hook in ["uv-post-netcat", "uv-on-upload-attempted"]:
			local("chmod +x .git/hooks/%s" % hook)
			
if __name__ == "__main__":
	base_dir = os.getcwd()
	monitor_root = os.path.join(base_dir, ".monitor")
	extras = {}
	
	if len(argv[1]) > 3:
		try:
			with open(argv[1], 'rb') as CONFIG: extras.update(json.loads(CONFIG.read()))
		except Exception as e: pass

	try:
		SSH_ROOT = extras['ssh_root']
	except Exception as e:
		print "Where is your server's ssh root?"
		SSH_ROOT = prompt("[DEFAULT: ~/.ssh]")

		if len(SSH_ROOT) == 0:
			SSH_ROOT = os.path.join(os.path.expanduser("~"), ".ssh")

	if not os.path.exists(SSH_ROOT):
		with settings(warn_only=True):
			local("mkdir %s" % SSH_ROOT)
	
	try:
		annex_dir = extras['annex_dir']
	except Exception as e:
		print "Where should Unveillace host its files?"
		annex_dir = prompt("[DEFAULT: ~/unveillance_remote]")

		if len(annex_dir) == 0:
			annex_dir = os.path.join(os.path.expanduser("~"), "unveillance_remote")

	try:
		uv_server_host = extras['uv_server_host']
	except Exception as e:
		print "What is the PUBLIC IP/hostname of this server?"
		uv_server_host = prompt("[DEFAULT: localhost]")

		if len(uv_server_host) == 0:
			uv_server_host = "127.0.0.1"
	
	try:
		uv_uuid = extras['uv_uuid']
	except Exception as e:
		print "What is this server's short name?"
		uv_uuid = prompt("Pressing enter will generate a default")
		
		if len(uv_uuid) == 0:
			from time import time
			uv_uuid = "unveillance_annex_%d" % time()
	
	try:
		uv_log_cron = extras['uv_log_cron']
	except Exception as e:
		print "Unveillance tasks might log a lot of information.  How frequently would you like the logs to be cleared?"
		uv_log_cron = prompt("[DEFAULT: 3 days]")
		
		if len(uv_log_cron) == 0:
			uv_log_cron = 3

	if type(uv_log_cron) is not int:
		uv_log_cron = 3

	with settings(warn_only=True):
		local("mkdir %s" % annex_dir)	
		local("mkdir %s" % monitor_root)
		PYTHON_HOME = local('which python', capture=True)
		SYS_ARCH = local("uname -m", capture=True)
		
	cron = CronTab(tab='# Unveillance CronTab')
	cron_job = cron.new(
		command="%s %s >> %s" % (PYTHON_HOME, os.path.join(base_dir, 'clear_logs.py'), os.path.join(monitor_root, "api.log.txt")),
		comment="clear_logs")

	cron_job.every(uv_log_cron).days()
	cron_job.enable()
	
	cron.write(os.path.join(monitor_root, "uv_cron.tab"))	

	print "******************************************"
	els_root = locateLibrary(r'elasticsearch*')
	if els_root is None:
		with settings(warn_only=True):
			local("wget -O lib/elasticsearch.tar.gz https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.tar.gz")
			local("tar -xvzf lib/elasticsearch.tar.gz -C lib")
			local("rm lib/elasticsearch.tar.gz")

		els_root = locateLibrary(r'elasticsearch*')
	else:
		print "Elasticsearch downloaded; moving on..."
	
	with open(os.path.join(os.path.expanduser("~"), ".bash_profile"), 'ab') as BASHRC:
		BASHRC.write("export UV_SERVER_HOST=\"%s\"\n" % uv_server_host)
		BASHRC.write("export UV_UUID=\"%s\"\n" % uv_uuid)
	
	with open(os.path.join(base_dir, "conf", "annex.config.yaml"), "wb+") as CONFIG:
		CONFIG.write("base_dir: %s\n" % base_dir)
		CONFIG.write("annex_dir: %s\n" % annex_dir)
		CONFIG.write("els_root: %s\n" % os.path.join(els_root, "bin", "elasticsearch"))
		CONFIG.write("monitor_root: %s\n" % monitor_root)
		CONFIG.write("sys_arch: %s\n" % SYS_ARCH)
		CONFIG.write("python_home: %s\n" % PYTHON_HOME)
		CONFIG.write("ssh_root: %s\n" % SSH_ROOT)
		CONFIG.write("uv_log_cron: %d\n" % uv_log_cron)
	
	with open(os.path.join(base_dir, "conf", "annex.config.yaml"), "ab") as CONFIG:
		from lib.Core.Utils.funcs import generateNonce
		CONFIG.write("document_salt: \"%s\"\n" % generateNonce())
	
	initAnnex(annex_dir, base_dir, PYTHON_HOME)
	os.chdir(base_dir)
	
	exit(0)