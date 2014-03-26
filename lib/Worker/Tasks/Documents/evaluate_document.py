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
	from lib.Worker.Utils.funcs import hashEntireFile, getFileType
	from Models.uv_object import UnveillanceObject
	
	document = UnveillanceObject()
	document.file_name = task.file_name
	document.id = hashEntireFile(os.path.join(ANNEX_DIR, document.file_name))
	document.mime_type = getFileType(os.path.join(ANNEX_DIR, document.file_name))
	print document.emit()
	
	if document.mime_type not in MimeTypes.EVALUATE:
		print "COULD NOT IDENTIFY MIME TYPE AS USABLE"
		return
	
	# DOING THIS THE HARD WAY: UUID MUST BE TRANSLATED IN NGINX TO CORRECT FARM ?
	# DRIZZLE (http://wiki.nginx.org/NginxHttpDrizzleModule)
	document.farm = UUID
	document.addAsset(task.file_name, None, 
		description="original version of document", tags=[AssetTypes.ORIG])

	# Iterate through task manifest to find establish route?
		
	print document.emit()
	print "\n\n************** DOCUMENT EVALUATION [END] ******************\n"