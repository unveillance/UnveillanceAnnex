from __future__ import absolute_import

from lib.Worker.vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateDocument(task):
	print "\n\n************** DOCUMENT EVALUATION [START] ******************\n"
	print "evaluating document at %s" % task.file_name
	task.setStatus(412)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG, UUID
	
	document = UnveillanceDocument(inflate={'file_name' : task.file_name})
	if DEBUG: print document.emit()
	
	if hasattr(document, 'invalid') and document.invalid:
		print "\n\n************** DOCUMENT EVALUATION [INVALID] ******************\n"
		print "DOCUMENT INVALID"
		
		task.invalidate(error="DOCUMUENT INVALID")
		return
	
	from lib.Core.vars import AssetTags
	from lib.Worker.Models.uv_task import UnveillanceTask
	
	document.addAsset(task.file_name, None, as_original=True,
		description="original version of document", tags=[AssetTags.ORIG])

	# Iterate through task manifest to find establish route?
		
	if DEBUG: print document.emit()
	
	task.setStatus(200)
	print "\n\n************** DOCUMENT EVALUATION [END] ******************\n"