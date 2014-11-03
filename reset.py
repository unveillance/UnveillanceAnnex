import os
from sys import exit
from fabric.api import local, settings
from fabric.operations import prompt
from crontab import CronTab

from conf import DEBUG, ANNEX_DIR, MONITOR_ROOT, BASE_DIR, getConfig
from Utils.funcs import forceQuitUnveillance
from setup import initAnnex

if __name__ == "__main__":
	this_dir = os.getcwd()
	annex_includes = None
	restore_from = None

	try:
		annex_includes = getConfig('annex_includes')
	except KeyError as e: pass

	print "****************************** [ IMPORTANT!!!! ] ******************************"
	print "Do you want to save the documents added to your annex so far? (y or n)"
	do_evacuate = False if prompt("[DEFAULT y]: ") == "n" else True

	if do_evacuate:
		from evacuate import evacuate

		default_evac_root = os.path.join(os.path.expanduser('~'), "UNVEILLANCE_MEDIA_EVACUATED")

		print "Where should these documents be evacuated to?"
		print "i.e. /full/path/to/root"
		evac_root = prompt("[DEFAULT %s]: " % default_evac_root)
		if len(evac_root) == 0:
			evac_root = default_evac_root

		try:
			restore_from = evacuate(evac_root=evac_root, omit_list=annex_includes)[0]
		except:
			print "Evacuation failed.  Continue? (y or n)"
			if prompt("[DEFAULT n]: ") != "y":
				exit(-1)
	
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

		# TODO: this should be sudoered for the unveillance user
		print "****************************** [ IMPORTANT!!!! ] ******************************"
		print "The next command requires sudo."
		print "If you can do sudo without a password, press ENTER."
		print "Or else, type it in here"
		sudo_pwd = prompt("[DEFAULT None]: ")

		local("%s rm -rf .git" % ("sudo" if len(sudo_pwd) == 0 else "echo \"%s\n\" | sudo -S" % sudo_pwd))
		local("rm *")

		initAnnex(ANNEX_DIR, BASE_DIR, getConfig('git_annex_bin'), MONITOR_ROOT, getConfig('python_home'))

		os.chdir(ANNEX_DIR)
		if annex_includes is not None:
			for _, _, files in os.walk(annex_includes):
				for f in files:
					local("cp %s ." % os.path.join(annex_includes, f))
					local("%s add %s" % (os.path.join(getConfig('git_annex_bin'), "git-annex"), f))

				# this should not be recursive.
				break

		local("%s sync" % os.path.join(getConfig('git_annex_bin'), "git-annex"))
		os.chdir(this_dir)

	if restore_from is not None: exit(1)

	exit(0)