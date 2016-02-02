from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateText(task):
	task_tag = "TEXT EVALUATION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "evaluating text at %s" % task.doc_id
	task.setStatus(302)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG
	from vars import MIME_TYPE_TASKS
	
	document = UnveillanceDocument(_id=task.doc_id)	
	"""
		limited choices: json, pgp, or txt
	"""

	if hasattr(task, "text_file"):
		content = document.loadAsset(task.text_file)
	else:
		content = document.loadFile(document.file_name)	
	
	if content is None:
		print "no text to evaluate :("
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
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
		
		if document.mime_type in MIME_TYPE_TASKS.keys():
			task_path = MIME_TYPE_TASKS[document.mime_type][0]
	else:
		try:
			from lib.Core.Utils.funcs import cleanLine
			from vars import ASSET_TAGS
			
			txt_json = []
			txt_pages = []
			line_count = 0
			
			# this is arbitrary
			MAX_LINES_PER_PAGE = 80
			
			for line in content.splitlines():
				txt_pages.append(cleanLine(line))
				line_count += 1
				
				if line_count == MAX_LINES_PER_PAGE:
					txt_json.append(" ".join(txt_pages))
					txt_pages = []
					line_count = 0

			txt_json.append(" ".join(txt_pages))

			document.total_pages = len(txt_json)
			document.save()
						
			asset_path = document.addAsset(txt_json, "doc_texts.json", as_literal=False,
				description="jsonified text of original document, segment by segment",
				tags=[ASSET_TAGS['TXT_JSON']])

			from lib.Worker.Models.uv_text import UnveillanceText
			uv_text = UnveillanceText(inflate={
				'media_id' : document._id,
				'searchable_text' : txt_json,
				'file_name' : asset_path
			})
			
			document.text_id = uv_text._id
			document.save()
		except Exception as e: 
			if DEBUG:
				print "ERROR HERE GENERATING DOC TEXTS:"
				print e
	
	document.addCompletedTask(task.task_path)
	task.finish()
	task.routeNext()
	print "\n\n************** %s [END] ******************\n" % task_tag