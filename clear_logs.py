import os, re
from fabric.api import settings, local
from fabric.context_managers import hide

if __name__ == "__main__":
	from conf import MONITOR_ROOT
	
	os.chdir(MONITOR_ROOT)
	for _, _, files in os.walk(MONITOR_ROOT):
		for file in files:
			log_match = re.match(r'.+\.log\.txt$', file)
			if log_match is not None:
				with settings(hide('everything'), warn_only=True): 
					local("truncate -s 0 %s" % file)
		break