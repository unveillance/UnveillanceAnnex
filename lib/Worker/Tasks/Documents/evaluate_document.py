from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateDocument(task):
	task_tag = "DOCUMENT EVALUATION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "evaluating document at %s" % task.file_name
	task.setStatus(412)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG, UUID
	
	document = None
	
	if hasattr(task, "doc_id"):
		document = UnveillanceDocument(_id=task.doc_id)
	else:
		document = UnveillanceDocument(inflate={'file_name' : task.file_name})
	
	if document is None:
		print "\n\n************** %s [INVALID] ******************\n" % task_tag
		print "DOCUMENT INVALID"
		
		task.invalidate(error="DOCUMUENT INVALID")
		return
		
	if hasattr(document, 'invalid') and document.invalid:
		print "\n\n************** %s [INVALID] ******************\n" % task_tag
		print "DOCUMENT INVALID"
		
		task.invalidate(error="DOCUMUENT INVALID")
		return
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	from vars import MIME_TYPE_TASKS
	
	if document.mime_type in MIME_TYPE_TASKS.keys():
		if DEBUG:
			print "mime type (%s) usable..." % document.mime_type
			print MIME_TYPE_TASKS[document.mime_type][0]
		
		new_task = UnveillanceTask(inflate={
			'task_path' : MIME_TYPE_TASKS[document.mime_type][0],
			'doc_id' : document._id,
			'queue' : task.queue
		})
		
		if DEBUG: print new_task.emit()
		new_task.run()
		
	else:
		if DEBUG: print "mime type (%s) not important" % document.mime_type
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag