import os
from importlib import import_module
from multiprocessing import Process

from Models.uv_object import UnveillanceObject
from lib.Core.vars import EmitSentinel, UVDocType
from Utils.funcs import printAsLog
from lib.Worker.vars import TASKS_ROOT

from conf import DEBUG, BASE_DIR

class UnveillanceTask(UnveillanceObject):
	def __init__(self, inflate=None, _id=None):		
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash()
			inflate['uv_doc_type'] = UVDocType.TASK
			inflate['status'] = 404
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, 
			emit_sentinels=[EmitSentinel("ctx", "Worker", None)])
	
	def run(self, ctx):
		# i.e. "lib.Worker.Tasks.Documents.evaluate_document"
		task_path = ".".join([TASKS_ROOT, self.task_path])
		p, f = task_path.rsplit(".", 1)

		try:
			module = import_module(p)
			func = getattr(module, f)
			args = [(self,), ({'queue' :self.queue})]
			if DEBUG: print args
			
			from lib.Worker.Tasks.Documents.evaluate_document import evaluateDocument
			evaluateDocument(self)
			
			#p = Process(target=func.apply_async, args=args)
			#p.start()
		except Exception as e:
			printAsLog(e)
	
	def finish(self):
		if DEBUG: print "task finished!"
		self.setStatus(200)
	
	def setStatus(self, status):
		self.status = status
		self.save()