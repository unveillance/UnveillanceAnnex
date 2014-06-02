from Models.uv_object import UnveillanceObject

class UnveillanceBatch(UnveillanceObject):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash(content="".join(inflate['documents']))
		
		super(UnveillanceBatch, self).__init__(_id=_id, inflate=inflate)