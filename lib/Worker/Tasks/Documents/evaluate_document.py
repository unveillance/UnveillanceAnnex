from __future__ import absolute_import

from lib.Worker.vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateDocument(task):
	print "\n\n************** DOCUMENT EVALUATION [START] ******************\n"
	print "evaluating document at %s" % task.file_name
	
	if not task.ctx.fileExistsInAnnex(task.file_name, auto_add=False):
		print "THIS FILE DOES NOT EXIST"
		return
	
	from Models.uv_document import UnveillanceDocument
	from conf import DEBUG
	
	document = UnveillanceDocument(inflate={ 'file_name' : task.file_name }) 
	if DEBUG: print document.emit()
	
	if document.invalid:
		print "\n\n************** DOCUMENT EVALUATION [INVALID] ******************\n"
		return
	
	from lib.Worker.vars import AssetTypes
	from lib.Worker.Models.uv_task import UnveillanceTask
	
	document.addAsset(task.file_name, None, as_original=True,
		description="original version of document", tags=[AssetTypes.ORIG])

	# Iterate through task manifest to find establish route?
		
	if DEBUG: print document.emit()
	print "\n\n************** DOCUMENT EVALUATION [END] ******************\n"