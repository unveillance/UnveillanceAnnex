from __future__ import absolute_import

from lib.Worker.vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateDocument(task):
	print "\n\n************** DOCUMENT EVALUATION [START] ******************\n"
	print "evaluating document at %s" % task.file_name
	
	if not task.ctx.fileExistsInAnnex(task.file_name, auto_add=False):
		print "THIS FILE DOES NOT EXIST"
		return
	
	import os
	from conf import ANNEX_DIR, UUID
	
	from lib.Worker.vars import MimeTypes
	from lib.Worker.Models.uv_task import UnveillanceTask
	
	from lib.Core.Utils.funcs import hashEntireFile
	from lib.Worker.Utils.funcs import getFileType 
	from Models.uv_object import UnveillanceObject
	
	doc_inflate = {
		'file_name' : task.file_name,
		'_id' : hashEntireFile(os.path.join(ANNEX_DIR, task.file_name)),
		'mime_type' : getFileType(os.path.join(ANNEX_DIR, task.file_name))
	}
	
	document = UnveillanceObject(inflate=doc_inflate) 
	print document.emit()
	
	if document.mime_type not in MimeTypes.EVALUATE:
		print "COULD NOT IDENTIFY MIME TYPE AS USABLE"
		return
	
	document.farm = UUID
	document.addAsset(task.file_name, None, as_original=True,
		description="original version of document", tags=[AssetTypes.ORIG])

	# Iterate through task manifest to find establish route?
		
	print document.emit()
	print "\n\n************** DOCUMENT EVALUATION [END] ******************\n"