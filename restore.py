from sys import exit, argv

def restore(top=None):
	import os
	from time import sleep
	from fabric.api import settings, local
	from fabric.operations import prompt

	default_evac_dir = os.path.join(os.path.expanduser('~'), "UNVEILLANCE_MEDIA_EVACUATED")
	print "****************************** [ IMPORTANT!!!! ] ******************************"
	print "Unveillance is about to restore evacuated documents."
	print "These documents should be found in %s" % default_evac_dir
	print "Please confirm this is the right directory (i.e. /full/path/to/dir):"
	
	evac_dir = prompt("[DEFAULT %s]: " % default_evac_dir)
	if len(evac_dir) == 0:
		evac_dir = default_evac_dir

	if not os.path.exists(evac_dir): return False

	from json import loads
	from vars import GIT_ANNEX_METADATA
	from conf import ANNEX_DIR, getConfig
	from sync_file import sync_file

	GIT_ANNEX = os.path.join(getConfig('git_annex_bin'), 'git-annex')
	this_dir = os.getcwd()
	cmd_tmpl = ["cp %s %s && %s add %s", "%s metadata \"%s\" --set=%s=%s"]
	
	with open(os.path.join(evac_dir, "evac_manifest.json"), 'rb') as m:
		manifest = loads(m.read())

	count = 0
	os.chdir(ANNEX_DIR)
	for _, _, files in os.walk(evac_dir):
		for file in [file for file in files if file != "evac_manifest.json"]:
			try:
				dm = [dm for dm in manifest if dm['file_name'] == file][0]
			except Exception as e:
				print e
				continue

			cmd = cmd_tmpl[0] % (os.path.join(evac_dir, file), ANNEX_DIR, GIT_ANNEX, file)
			with settings(warn_only=True): local(cmd)

			for f in GIT_ANNEX_METADATA:
				if f in dm.keys():
					cmd = cmd_tmpl[1] % (GIT_ANNEX, file, f,
						"\"%s\"" % dm[f] if type(dm[f]) in [str, unicode] else dm[f])
					
					with settings(warn_only=True): local(cmd)
			
			sync_file(file)
			sleep(5)
			count += 1

			print "TOP: %s" % type(top)
			print top

			if type(top) is int and count >= top:
				print "MAX REQUESTED IMPORTED"
				break

		break

	os.chdir(this_dir)
	return True

if __name__ == "__main__":
	top = None
	if len(argv) == 2: top = int(argv[1])
	if not restore(top=top): exit(-1)
	exit(0)