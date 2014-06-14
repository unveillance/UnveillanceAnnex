import re, os
from sys import argv, exit
from time import sleep
from fabric.api import local
from fabric.operations import prompt

if __name__ == "__main__":
	base_dir = os.getcwd()
	
	annex_dir = prompt("Where should Unveillace host its files?\n[DEFAULT: ~/unveillance_remote")
	if len(annex_dir) == 0: annex_dir = "~/unveillance_remote"
	
	local("mkdir %s" % annex_dir)
	local("mkdir .monitor")
	
	local("wget -O lib/elasticsearch.tar.gz https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.tar.gz")
	local("tar -xvzf lib/elasticsearch.tar.gz -C lib")
	local("rm lib/elasticsearch.tar.gz")
	
	local("wget -O lib/git-annex.tar.gz http://downloads.kitenet.net/git-annex/linux/current/git-annex-standalone-amd64.tar.gz")
	local("tar -xvzf lib/git-annex.tar.gz -C lib")
	local("rm lib/git-annex.tar.gz")
	
	git_annex_dir = None
	els_dir = None
	
	for _, dir, files in os.walk(os.path.join(base_dir, "lib")):
		print dir
		
	
	with open(os.path.join(base_dir, "conf", "annex.config.yaml"), "wb+") as CONFIG:
		CONFIG.write("base_dir: %s\n" % base_dir)
		CONFIG.write("annex_dir: %s\n" % annex_dir)
		CONFIG.write("els_root: %s\n" % els_dir)
		CONFIG.write("git_annex_bin: %s\n" % git_annex_dir)
	
	os.chdir(os.path.join(base_dir, "lib", "Core"))
	local("pip install --upgrade -r requirements.txt")
	
	os.chdir(base_dir)
	local("pip install --upgrade -r requirements.txt")
	
	exit(0)