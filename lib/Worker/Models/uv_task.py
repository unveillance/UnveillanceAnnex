from multiprocessing import Process

from Models.uv_object import UnveillanceObject
from Models.vars import EmitSentinel
from Utils.funcs import printAsLog
from lib.Worker.vars import TASKS_ROOT

class UnveillanceTask(UnveillanceObject):
	def __init__(self, args**):
		if inflate is not None:
			inflate['_id'] = generateMD5Hash()
			inflate['status'] = 404
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, emit_sentinels=[
			EmitSentinel("ctx", "Worker", None)])
	
	def run(self, ctx):
		self.ctx = ctx
		
		# i.e. "lib.Worker.Tasks.Documents.evaluate_document"
		module = __import__(".".join([TASKS_ROOT, self.task_path]))
				
		p = Process(target=module.apply_sync, args=((self,), queue=self.queue)
		p.start()
	
	def setStatus(self, status):
		self.status = status
		self.save()