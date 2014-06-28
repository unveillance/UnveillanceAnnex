import os, re
from fabric.api import settings, local

if __name__ == "__main__":
	from conf import MONITOR_ROOT
	
	os.chdir(MONITOR_ROOT)
	for _, _, files in os.walk(MONITOR_ROOT):
		for file in files:
			if re.match(r'.+\.log\.txt', file):
				with settings(warn_only=True): local("rm %s" % file)
		break