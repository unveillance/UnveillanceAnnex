from Models.uv_object import UnveillanceObject
from Utils.funcs import printAsLog

class UnveillanceTask(UnveillanceObject):
	def __init__(self, ctx, is_private=True, **extras):
		super(UnveillanceTask, self).__init__()
		
		self.ctx = ctx
		self.is_private = is_private
		
		print extras
		for k,v in extras.iteritems():
			setattr(self, k, v)
		
		
		print self.emit()