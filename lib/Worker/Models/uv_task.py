import os
from time import sleep
from importlib import import_module
from multiprocessing import Process

from Models.uv_object import UnveillanceObject
from Utils.funcs import printAsLog

from vars import EmitSentinel, UV_DOC_TYPE, TASKS_ROOT
from conf import DEBUG, BASE_DIR

class UnveillanceTask(UnveillanceObject):
	def __init__(self, inflate=None, _id=None):		
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash()
			inflate['uv_doc_type'] = UV_DOC_TYPE['TASK']
			inflate['status'] = 404
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, 
			emit_sentinels=[EmitSentinel("ctx", "Worker", None)])
	
	def run(self):
		# i.e. "lib.Worker.Tasks.Documents.evaluate_document"
		task_path = ".".join([TASKS_ROOT, self.task_path])
		p, f = task_path.rsplit(".", 1)

		try:
			module = import_module(p)
			func = getattr(module, f)

			#TODO: for cellery: 
			# args = [(self,), ({'queue' :self.queue})]

			args = [self]
			if DEBUG: print args
			
			#p = Process(target=func.apply_async, args=args)
			p = Process(target=func, args=args)
			p.start()
		except Exception as e:
			printAsLog(e)
	
	def finish(self):
		if DEBUG: print "task finished!"
		
		if not hasattr(self, 'persist') or not self.persist:
			self.setStatus(200)
			if DEBUG: print "task will be deleted!"
			self.delete()
		else:
			self.setStatus(205)
			self.save()
			if DEBUG: print "task will run again after %d minutes" % self.persist
			sleep(self.persist * 60)
			self.run()
	
	def delete(self):
		if DEBUG: print "DELETING MYSELF"
		return super(UnveillanceTask, self).delete(self._id)
	
	def setStatus(self, status):
		self.status = status
		self.save()