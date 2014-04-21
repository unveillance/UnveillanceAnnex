from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateFile(task):
	task_tag = "EVALUATING DOCUMENT (INFORMACAM)"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	document = UnveillanceDocument(_id=task.doc_id)
	if document is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if not document.getFile(document.file_name):
		print "NO DOCUMENT CONTENT"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	content = document.loadFile(document.file_name)
	if content is None: return