from multiprocessing import Process

from Models.uv_object import UnveillanceObject
from lib.Core.vars import EmitSentinel
from Utils.funcs import printAsLog
from lib.Worker.vars import TASKS_ROOT

from conf import DEBUG

class UnveillanceTask(UnveillanceObject):
	def __init__(self, **args):
		if inflate is not None:
			inflate['_id'] = generateMD5Hash()
			inflate['status'] = 404
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, emit_sentinels=[
			EmitSentinel("ctx", "Worker", None)])
	
	def run(self, ctx):
		self.ctx = ctx
		
		# i.e. "lib.Worker.Tasks.Documents.evaluate_document"
		func = __import__(".".join([TASKS_ROOT, self.task_path]))

		# func.apply_sync((task,) queue=queue_name)	
		args = [(self,), (queue,self.queue)]
		if DEBUG: print args
					
		p = Process(target=func.apply_sync, args=args)
		p.start()
	
	def setStatus(self, status):
		self.status = status
		self.save()