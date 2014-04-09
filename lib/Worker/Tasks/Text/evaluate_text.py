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
	new_mime_type = None
	
	import json
	try:
		json_txt = json.loads(content)
		new_mime_type = "application/json"
		
		print "THIS IS JSON"
	except Exception as e:
		print "NOT JSON: %s" % e
	
	task_path = None
	if new_mime_type is not None:
		document.mime_type = new_mime_type
		document.save()
		
		from vars import MIME_TYPE_TASKS
		if document.mime_type in MIME_TYPE_TASKS.keys():
			task_path = MIME_TYPE_TASKS[document.mime_type][0]
	else:
		try:
			task_path = MIME_TYPE_TASKS[document.mime_type][1]
		except Exception as e: print e
	
	if task_path is not None:
		from lib.Worker.Models.uv_task import UnveillanceTask
		new_task = UnveillanceTask(inflate={
			'doc_id' : document._id,
			'task_path' : ,
			'queue' : UUID})
		new_task.run(task)