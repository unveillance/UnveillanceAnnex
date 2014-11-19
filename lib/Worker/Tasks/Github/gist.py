from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def run_gist(uv_task):
	task_tag = "RUNNING USER GIST"

	if not hasattr(uv_task, "gist_id"):
		error_msg = "Gist ID missing."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_msg)
		return

	import requests
	try:
		r = requests.get("https://api.github.com/gists/%s" % uv_task.gist_id)
	except Exception as e:
		error_msg = "Cannot connect to Github API"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_msg)
		return

	import json
	try:
		gist = json.loads(r.content)['files']['raw_rul']
	except Exception as e:
		error_msg = "Cannot get URL to gist %s" % uv_task.gist_id
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_msg)
		return

	print "\n\n************** %s [END] ******************\n" % task_tag
	uv_task.finish()