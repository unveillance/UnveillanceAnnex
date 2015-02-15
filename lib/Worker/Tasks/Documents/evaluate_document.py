from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateDocument(uv_task):
	task_tag = "DOCUMENT EVALUATION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	uv_task.setStatus(302)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG, UUID
	
	document = None
	
	if hasattr(uv_task, "doc_id"):
		if DEBUG:
			print "GETTING A DOCUMENT FROM ID: %s" % uv_task.doc_id
		
		document = UnveillanceDocument(_id=uv_task.doc_id)
	else:
		if DEBUG:
			print "INFLATING NEW DOCUMENT WITH FILE NAME: %s" % uv_task.file_name
		
		document = UnveillanceDocument(inflate={'file_name' : uv_task.file_name})
	
	if document is None:
		print "\n\n************** %s [INVALID] ******************\n" % task_tag
		print "DOCUMENT INVALID (is None)"
		
		uv_task.fail(message="DOCUMUENT INVALID (is none)")
		return
			
	from lib.Worker.Models.uv_task import UnveillanceTask
	from vars import MIME_TYPE_TASKS, MIME_TYPES
	
	document.addCompletedTask(uv_task.task_path)
	uv_task.put_next(uv_task.task_path)
	
	mime_type = document.query_mime_type()
		
	if mime_type in MIME_TYPE_TASKS.keys():
		if DEBUG:
			print "mime type (%s) usable..." % mime_type
			print MIME_TYPE_TASKS[mime_type]

		uv_task.put_next(MIME_TYPE_TASKS[mime_type])
		
	else:
		uv_task.fail(status=412, message="document mime type (%s) not important" % mime_type)
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	inflate = {'doc_id' : document._id}
	if mime_type == MIME_TYPES['symlink']:
		inflate['attempt_sync'] = True
		
	uv_task.routeNext(inflate=inflate)

	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
	