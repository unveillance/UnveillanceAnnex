from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def pullFromAnnex(uv_task):
	task_tag = "PULL FROM ANNEX"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "pulling file from document %s from annex" % uv_task.doc_id
	uv_task.setStatus(302)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG, BASE_DIR, getConfig
	
	document = UnveillanceDocument(_id=uv_task.doc_id)
	if document is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	if not document.getFile(document.file_name):
		print "NO FILE CONTENT"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	if hasattr(uv_task, "atttempt_sync") and uv_task.attempt_sync:
		from fabric.api import settings, local
		with settings(warn_only=True):
			local("%s %s %s" % (getConfig('python_home'), 
				os.path.join(BASE_DIR, "sync_file.py"), document.file_name))
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag