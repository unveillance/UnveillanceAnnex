import os, requests
from sys import argv, exit

if __name__ == "__main__":
	from Models.uv_elasticsearch import UnveillanceElasticsearchHandler

	from Utils.funcs import printAsLog
	from conf import HOST, API_PORT
	from vars import UPLOAD_RESTRICTION

	try:
		if argv[2] == UPLOAD_RESTRICTION['for_local_use_only']:
			from fabric.api import settings, local
			from conf import getConfig

			with settings(warn_only=True):
				local("%s metadata --tag uv_restricted %s" % (
					os.path.join(getConfig('git_annex_bin'), "git-annex"), argv[1]))

	except Exception as e:
		printAsLog(e, as_error=True)
		pass

	
	try:
		r = requests.post("http://%s:%d/sync/%s" % (HOST, API_PORT, argv[1]))
	except Exception as e:
		printAsLog(e, as_error=True)
		exit(1)
	
	exit(0)
