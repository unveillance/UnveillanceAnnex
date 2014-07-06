from lib.Worker.Models.uv_document import UnveillanceDocument

class UnveillanceText(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash(content=inflate['media_id'], salt="UV_TEXT")
		
		super(UnveillanceText, self).__init__(_id=_id, inflate=inflate)
