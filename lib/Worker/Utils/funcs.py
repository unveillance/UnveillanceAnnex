import magic, gzip, re
from cStringIO import StringIO
from json import loads

from conf import DEBUG

def routeNextTask(task, document, task_extras=None):
	if not hasattr(task, 'no_continue') or not task.no_continue:
		next_task_path = None
		
		from lib.Worker.Models.uv_task import UnveillanceTask
		
		if hasattr(task, 'next_task_path'):
			next_task_path = task.next_task_path
		else:
			from vars import MIME_TYPE_TASKS
		
			if document.mime_type in MIME_TYPE_TASKS.keys():
				try:
					next_task_path = MIME_TYPE_TASKS[document.mime_type][1]
				except Exception as e:
					if DEBUG: print e				
		
		if next_task_path is not None:
			inflate = {
				'task_path' : next_task_path,
				'doc_id' : document._id,
				'queue' : task.queue
			}
			
			if task_extras is not None: inflate.update(task_extras)
			
			next_task = UnveillanceTask(inflate=inflate)
			next_task.run()

def getFileType(file, as_buffer=False, force_json=False):
	m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
	try:
		if not as_buffer:
			mime_type = m.id_filename(file)
		else:
			mime_type = m.id_buffer(file)

		m.close()

		if mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
			mime_type = "application/word"
		
		if re.match(r'text/x\-.*', mime_type) is not None:
			mime_type = "text/plain"
		
		if mime_type == "text/plain" or (force_json and mime_type in ["text/plain", "application/octet-stream"]):
			if DEBUG:
				print "FORCING JSON ON MIME TYPE %s" % mime_type
				
			content = file
			if not as_buffer:
				with open(file, 'rb') as C:
					content = C.read()
			
			try:
				loads(content)
				mime_type = "application/json"
			except Exception as e:
				if DEBUG:
					print e, type(e)
					print "NOT JSON"
			
		return mime_type
		
	except Exception as e:
		if DEBUG:
			print "** ERROR GETTING MIME TYPE : %s (type %s)***" % (e, type(e))

		pass
	
	m.close()
	return None

def gzipFile(path):
	_out = StringIO()
	_in = open(path)
	
	z = gzip.GzipFile(fileobj=_out, mode='w')
	z.write(_in.read())
	
	z.close()
	_in.close()
	
	return _out.getvalue()

def unGzipBinary(bin):
	try:
		with gzip.GzipFile(fileobj=StringIO(bin)) as G:
			return G.read()
			
	except Exception as e:
		return None

def unGzipFile(path):
	try:
		with gzip.GzipFile(path, 'rb') as G:
			return G.read()
			
	except Exception as e:
		return None