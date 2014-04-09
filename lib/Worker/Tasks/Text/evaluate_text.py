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
