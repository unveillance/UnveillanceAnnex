import os, requests
from sys import argv, exit

if __name__ == "__main__":
	from Utils.funcs import printAsLog
	from conf import HOST, API_PORT
	from vars import UPLOAD_RESTRICTION

	try:
		if argv[2] == UPLOAD_RESTRICTION['for_local_use_only']:
			from fabric.api import settings, local
			from conf import getConfig, ANNEX_DIR

			this_dir = os.getcwd()
			os.chdir(ANNEX_DIR)

			with settings(warn_only=True):
				local("git annex metadata %s --set=uv_restriction=%d" % (argv[1], argv[2]))

			os.chdir(this_dir)

	except Exception as e:
		printAsLog(e, as_error=True)
		pass

	
	try:
		r = requests.post("http://%s:%d/sync/%s" % (HOST, API_PORT, argv[1]))
	except Exception as e:
		printAsLog(e, as_error=True)
		exit(1)
	
	exit(0)
