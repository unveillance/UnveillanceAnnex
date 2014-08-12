import os
from fabric.api import local, settings
from crontab import CronTab

from conf import ANNEX_DIR, MONITOR_ROOT, BASE_DIR, getConfig
from Utils.funcs import forceQuitUnveillance

if __name__ == "__main__":
	this_dir = os.getcwd()
	annex_includes = None
	
	try:
		annex_includes = getConfig('annex_includes')
	except KeyError as e: pass
	
	print "Force-Quitting old instance"
	forceQuitUnveillance()
		
	try:
		cron = CronTab(tabfile=os.path.join(MONITOR_ROOT, "uv_cron.tab"))
		for job in cron:
			job.enable(False)
		
		cron.remove_all()
		with settings(warn_only=True):
			local("crontab -r")
			local("rm %s" % os.path.join(MONITOR_ROOT, "uv_cron.tab"))

	except IOError as e:
		pass

	cron = CronTab(tab='# Unveillance CronTab')
	cron_job = cron.new(
		command="%s %s >> %s" % (getConfig('python_home'), os.path.join(BASE_DIR, 'clear_logs.py'), os.path.join(MONITOR_ROOT, "api.log.txt")),
		comment="clear_logs")

	try:
		uv_log_cron = getConfig('uv_log_cron')
	except Exception as e:
		uv_log_cron = None

	if uv_log_cron is None: uv_log_cron = 3
	
	cron_job.every(uv_log_cron).days()
	cron_job.enable()
	
	cron.write(os.path.join(MONITOR_ROOT, "uv_cron.tab"))
	
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