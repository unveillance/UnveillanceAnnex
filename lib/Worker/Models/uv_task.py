from Models.uv_object import UnveillanceObject
from Models.vars import EmitSentinel
from Utils.funcs import printAsLog

class UnveillanceTask(UnveillanceObject):
	def __init__(self, args**):
		try:
			self.ctx = ctx
		except Exception as e:
			print e
			return
			
		if inflate is not None:
			inflate['_id'] = generateMD5Hash()
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, emit_sentinels=[
			EmitSentinel("ctx", "Worker", None)])