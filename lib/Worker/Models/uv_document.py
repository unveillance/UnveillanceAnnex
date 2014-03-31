from Models.uv_object import UnveillanceObject
from lib.Core.vars import MimeTypes
from lib.Core.funcs import hashEntireFile
from lib.Worker.funcs import getFileType

class UnveillanceDocument(UnveillanceObject):
	def __init__(self, args**):
	
		if inflate is not None:
			import os
			from conf import ANNEX_DIR, UUID
		
			mime_type = hashEntireFile(os.path.join(ANNEX_DIR, file_name))
			mime_type not in MimeTypes.EVALUATE:
				print "COULD NOT IDENTIFY MIME TYPE AS USABLE"
				self.invalidate()
				return
		
			inflate['_id'] = mime_type
			inflate['mime_type'] = getFileType(os.path.join(ANNEX_DIR, file_name))
			inflate['farm'] = UUID
		
		super(UnveillanceDocument, self).__init__(_id=_id, inflate=inflate)
	
	def invalidate(self): self.invalid = True
	