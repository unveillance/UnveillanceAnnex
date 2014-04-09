from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateText(task):
	print "\n\n************** TEXT EVALUATION [START] ******************\n"
	print "evaluating text at %s" % task.doc_id
	task.setStatus(412)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG
	
	document = UnveillanceDocument(_id=task.doc_id)
	if DEBUG: print document.emit()
	
	"""
		limited choices: json, pgp, or txt
	"""
	if not document.getFile(document.file_name): return
	
	content = document.loadAsset(document.file_name)
	
	import json
	try:
		json_txt = json.loads(content)
		document.mime_type = "application/json"
		document.save()
		
		print "THIS IS JSON"
	except Exception as e:
		print "NOT JSON: %s" % e
