import re, os, json
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

if __name__ == "__main__":
	base_dir = os.getcwd()
	monitor_root = os.path.join(base_dir, ".monitor")
	extras = {}
	
	if len(argv[1]) > 3:
		try:
			with open(argv[1], 'rb') as CONFIG: extras.update(json.loads(CONFIG.read()))
		except Exception as e: pass
	
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
		uv_uuid = config['uv_uuid']
	except Exception as e:
		print "What is this server's short name?"
		uv_uuid = prompt("Pressing enter will generate a default")
		
		if len(uv_uuid) == 0:
			from time import time
			uv_uuid = "unveillance_annex_%d" % time()
	
	with settings(warn_only=True):
		local("mkdir %s" % annex_dir)	
		local("mkdir %s" % monitor_root)

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
	
	git_annex_dir = locateLibrary(r'git-annex\.*')
	if git_annex_dir is None:
		with settings(warn_only=True):
			local("wget -O lib/git-annex.tar.gz http://downloads.kitenet.net/git-annex/linux/current/git-annex-standalone-amd64.tar.gz")
			local("tar -xvzf lib/git-annex.tar.gz -C lib")
			local("rm lib/git-annex.tar.gz")
		
		git_annex_dir = locateLibrary(r'git-annex\.*')
	else:
		print "Git Annex downloaded; moving on..."
	
	with open(os.path.join(os.path.expanduser("~"), ".bashrc"), 'ab') as BASHRC:
		BASHRC.write("export UV_SERVER_HOST=\"%s\"\n" % uv_server_host)
		BASHRC.write("export UV_UUID=\"%s\"\n" % uv_uuid)
		BASHRC.write("export PATH=$PATH:%s\n" % git_annex_dir)
	
	with open(os.path.join(base_dir, "conf", "annex.config.yaml"), "wb+") as CONFIG:
		CONFIG.write("base_dir: %s\n" % base_dir)
		CONFIG.write("annex_dir: %s\n" % annex_dir)
		CONFIG.write("els_root: %s\n" % os.path.join(els_root, "bin", "elasticsearch"))
		CONFIG.write("git_annex_bin: %s\n" % git_annex_dir)
		CONFIG.write("monitor_root: %s\n" % monitor_root)
	
	with open(os.path.join(base_dir, "conf", "annex.config.yaml"), "ab") as CONFIG:
		from lib.Core.Utils.funcs import generateNonce
		CONFIG.write("document_salt: %s\n" % generateNonce())
	
	os.chdir(annex_dir)
	with settings(warn_only=True):
		local("git init")
		local("mkdir .git/hooks")
		local("cp %s .git/hooks" % os.path.join(base_dir, "post-receive"))
		local("chmod +x .git/hooks/post-receive")
		local("git annex init \"unveillance_remote\"")
		local("git annex untrust web")
		local("git annex watch")

	os.chdir(base_dir)
	
	exit(0)