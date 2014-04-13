from Models.uv_object import UnveillanceObject
from conf import DEBUG

class UnveillanceDocument(UnveillanceObject):
	def __init__(self, _id=None, inflate=None):
	
		if inflate is not None:
			import os
			from lib.Core.Utils.funcs import hashEntireFile
			from conf import ANNEX_DIR, UUID
			from vars import UV_DOC_TYPE
		
			inflate['_id'] = hashEntireFile(os.path.join(ANNEX_DIR, inflate['file_name']))
			inflate['farm'] = UUID
			inflate['uv_doc_type'] = UV_DOC_TYPE['DOC']
		
		super(UnveillanceDocument, self).__init__(_id=_id, inflate=inflate)
		
		if inflate is not None:
			if not self.getFile(self.file_name):
				self.invalidate(error="COULD NOT GET DOCUMENT FROM ANNEX")
				return
				
			from lib.Worker.Utils.funcs import getFileType
			self.mime_type = getFileType(os.path.join(ANNEX_DIR, self.file_name))
			self.save()