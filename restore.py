def restore():
	from time import sleep
	from fabric.api import settings, local

	from conf import ANNEX_DIR, getConfig
	from sync_file import sync_file

	GIT_ANNEX = os.path.join(getConfig('git_annex_bin'), 'git-annex')
	this_dir = os.getcwd()
	evac_dir = os.path.join(os.path.expanduser('~'), "UNVEILLANCE_MEDIA_EVACUATED")
	cmd_tmpl = "cp %s %s && %s add %s"

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

if __name__ == "__main__": restore()