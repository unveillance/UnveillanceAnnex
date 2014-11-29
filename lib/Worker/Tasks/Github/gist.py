from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def run_gist(uv_task):
	task_tag = "RUNNING USER GIST"

	from conf import MASTER_GIST
	if MASTER_GIST is None:
		error_msg = "No Github master gist set up for this Annex."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_msg)
		return 

	if not hasattr(uv_task, "gist_id"):
		error_msg = "Gist ID missing."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	import requests
	gh = "https://api.github.com/gists"

	try:
		r = requests.get("%s/%s" % (gh, uv_task.gist_id))
	except Exception as e:
		error_msg = "Cannot connect to Github API"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_msg)
		return

	import json
	try:
		gh_res = json.loads(r.content)
		gist_manifest = gh_res['files']
		gist_raw_url = gist_manifest[gist_manifest.keys()[0]]['raw_url']
		gist_owner = gh_res['owner']['login']
	except Exception as e:
		error_msg = "Cannot get URL to gist %s" % uv_task.gist_id
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	# Now, if gist's author in our master gist of verified users?
	try:
		r = requests.get("%s/%s" % (gh, MASTER_GIST))
		m_gist_manifest = json.loads(r.content)['files']
		m_gist_raw_url = m_gist_manifest[m_gist_manifest.keys()[0]]['raw_url']
	except Exception as e:
		error_msg = "Cannot get URL to Master Gist"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	from fabric.api import settings, local
	try:
		with settings(warn_only=True):
			authorized_github_users = json.loads(local("wget -qO- %s" % m_gist_raw_url, capture=True))
	except Exception as e:
		error_msg = "Cannot get authorized users from master gist: %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	if gist_owner not in authorized_github_users:
		error_msg = "User %s not an authorized github user"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=401, message=error_msg)
		return

	with settings(warn_only=True):
		gist_func = local("wget -qO- %s" % gist_raw_url, capture=True)

	if gist_func is None or len(gist_func) == 0:
		error_msg = "No function here."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	gist_func = create_function_from_gist(gist_func)
	if gist_func is None:
		error_msg = "Could not compile function"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	try:
		gist_func.task_from_gist(uv_task)
	except Exception as e:
		error_msg = "GIST FUNCTION FAILED: %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	print "\n\n************** %s [END] ******************\n" % task_tag

	try:
		uv_task.finish()
	except Exception as e:
		print "task already finished???"
		print e
		print "\n\n************** %s [WARN] ******************\n" % task_tag

def create_function_from_gist(source):
	func = None
	
	import imp
	try:
		func = imp.new_module('task_from_gist')
		exec source in func.__dict__
	except Exception as e:
		print e
		return None
	
	return func