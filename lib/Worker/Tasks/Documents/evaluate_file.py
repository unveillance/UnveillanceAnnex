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
	
	if not document.getFile(task.file_name):
		print "NO FILE CONTENT"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
		
	from lib.Worker.Models.uv_task import UnveillanceTask
	from lib.Worker.Utils.funcs import getFileType
	from vars import MIME_TYPE_TASKS
	from conf import ANNEX_DIR
	
	try:
		mime_type = getFileType(os.path.join(ANNEX_DIR, task.file_name))
		new_task = UnveillanceTask(inflate={
			'task_path' : MIME_TYPE_TASKS[mime_type][0],
			'doc_id' : document._id,
			'file_name' : task.file_name
		})
		new_task.run()
	except IndexError as e:
		print "NO NEXT TASK: %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag