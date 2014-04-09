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
	from vars import AssetTags, MIME_TYPE_TASKS
	
	asset = document.addAsset(None, task.file_name, as_original=True,
		description="original version of document", tags=[AssetTags.ORIG])
	
	# Iterate through task manifest to find establish route to task
	new_task = None
	if document.mime_type in MIME_TYPE_TASKS.keys():
		new_task = UnveillanceTask(inflate={
			'task_path' : MIME_TYPE_TASKS[document.mime_type][0],
			'doc_id' : document._id,
			'queue' : task.queue})
	
	task.finish()
	if new_task is not None: new_task.run(task)
	print "\n\n************** DOCUMENT EVALUATION [END] ******************\n"
	