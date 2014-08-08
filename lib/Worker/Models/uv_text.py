from Models.uv_object import UnveillanceObject
from conf import DEBUG

class UnveillanceText(UnveillanceObject):
	def __init__(self, _id=None, inflate=None, emit_sentinels=None):
		if inflate is not None:
			import os
			from fabric.api import settings, local
			
			from lib.Core.Utils.funcs import generateMD5Hash
			from conf import UUID, ANNEX_DIR
			from vars import UV_DOC_TYPE, MIME_TYPES
			
			inflate['_id'] = generateMD5Hash(content=inflate['media_id'], 
				salt=MIME_TYPES['txt_stub'])
			
			inflate['farm'] = UUID
			inflate['uv_doc_type'] = UV_DOC_TYPE['DOC']
			inflate['mime_type'] = MIME_TYPES['txt_stub']
			
			this_dir = os.getcwd()
			os.chdir(ANNEX_DIR)
			
			file_name = "%s_%s" % (inflate['media_id'],
				inflate['file_name'].split("/")[-1])
				
			with settings(warn_only=True):
				ln = local("ln -s %s %s" % (inflate['file_name'], file_name),
					capture=True)
				
				if DEBUG: print ln
			
			os.chdir(this_dir)
			inflate['file_name'] = file_name
		
		super(UnveillanceText, self).__init__(_id=_id, 
			inflate=inflate, emit_sentinels=emit_sentinels)
			
	