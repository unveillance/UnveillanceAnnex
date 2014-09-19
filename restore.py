from sys import exit

def restore():
	from time import sleep
	from fabric.api import settings, local
	from fabric.operations import prompt

	from conf import ANNEX_DIR, getConfig
	from sync_file import sync_file

	GIT_ANNEX = os.path.join(getConfig('git_annex_bin'), 'git-annex')
	this_dir = os.getcwd()
	cmd_tmpl = "cp %s %s && %s add %s"

	default_evac_dir = os.path.join(os.path.expanduser('~'), "UNVEILLANCE_MEDIA_EVACUATED")
	print "****************************** [ IMPORTANT!!!! ] ******************************"
	print "Unveillance is about to restore evacuated documents."
	print "These documents should be found in %s" % default_evac_dir
	print "Please confirm this is the right directory (i.e. /full/path/to/dir):"
	
	evac_dir = prompt("[DEFAULT %s]: " % default_evac_dir)
	if len(evac_dir) == 0:
		evac_dir = default_evac_dir

	if not os.path.exists(evac_dir): return False

	os.chdir(ANNEX_DIR)
	for _, _, files in os.walk(evac_dir):
		for cmd in [cmd_tmpl % (evac_dir, file),
			ANNEX_DIR, GIT_ANNEX, file) for file in files]:
			with settings(warn_only=True):
				local(cmd)
				sync_file(file)
				sleep(5)
		break

	os.chdir(this_dir)
	return True

if __name__ == "__main__": 
	if not restore(): exit(-1)
	exit(0)