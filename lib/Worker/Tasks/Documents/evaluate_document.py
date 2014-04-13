from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateDocument(task):
	print "\n\n************** DOCUMENT EVALUATION [START] ******************\n"
	print "evaluating document at %s" % task.file_name
	task.setStatus(412)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG, UUID
	
	document = UnveillanceDocument(inflate={'file_name' : task.file_name})	
	if hasattr(document, 'invalid') and document.invalid:
		print "\n\n************** DOCUMENT EVALUATION [INVALID] ******************\n"
		print "DOCUMENT INVALID"
		
		task.invalidate(error="DOCUMUENT INVALID")
		return
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	from vars import MIME_TYPE_TASKS
	
	if document.mime_type in MIME_TYPE_TASKS.keys():
		print "mime type usable..."
		if DEBUG: print MIME_TYPE_TASKS[document.mime_type][0]
		
		new_task = UnveillanceTask(inflate={
			'task_path' : MIME_TYPE_TASKS[document.mime_type][0],
			'doc_id' : document._id,
			'queue' : task.queue
		})
		
		print new_task.emit()
		new_task.run()
		
	else:
		if DEBUG: print "mime type not important"
	
	task.finish()
	print "\n\n************** DOCUMENT EVALUATION [END] ******************\n"