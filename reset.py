import os
from fabric.api import local, settings
from crontab import CronTab

from conf import ANNEX_DIR, MONITOR_ROOT, getConfig

if __name__ == "__main__":
	this_dir = os.getcwd()
	annex_includes = getConfig('annex_includes')
	
	try:
		cron = CronTab(tabfile=os.path.join(MONITOR_ROOT, "uv_cron.tab"))
		for job in cron:
			job.enable(False)
		
		cron.remove_all()
		with settings(warn_only=True):
			local("rm %s" % os.path.join(MONITOR_ROOT, "uv_cron.tab"))

	except IOError as e:
		pass
	
	with settings(warn_only=True):
		os.chdir(ANNEX_DIR)
		local("rm -rf .data")
		local("git annex add .")
		local("git annex sync")
		local("rm *")
		local("git annex add .")
		local("git annex sync")
		local("mkdir .data")
		local("git annex add .")
		local("git annex sync")
	
		if annex_includes is not None:
			for _, _, files in os.walk(annex_includes):
				for f in files:
					local("cp %s ." % os.path.join(annex_includes, f))
					local("git annex add %s" % f)

				# this should not be recursive.
				break

		local("git annex sync")
		os.chdir(this_dir)