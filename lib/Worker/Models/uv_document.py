from Models.uv_object import UnveillanceObject

class UnveillanceDocument(UnveillanceObject):
	def __init__(self, _id=None, inflate=None, emit_sentinels=None):
	
		if inflate is not None:
			import os
			from lib.Core.Utils.funcs import hashEntireFile
			from conf import ANNEX_DIR, UUID
			from vars import UV_DOC_TYPE
		
			inflate['_id'] = hashEntireFile(os.path.join(ANNEX_DIR, inflate['file_name']))
			inflate['farm'] = UUID
			inflate['uv_doc_type'] = UV_DOC_TYPE['DOC']
		
		super(UnveillanceDocument, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=emit_sentinels)
		
		if inflate is not None:
			if not self.queryFile(self.file_name):
				self.invalidate(error="COULD NOT GET DOCUMENT FROM ANNEX")
				return
				
			from lib.Worker.Utils.funcs import getFileType
			self.mime_type = getFileType(os.path.join(ANNEX_DIR, self.file_name))
			
			if self.mime_type == "inode/symlink" and self.getFile(self.file_name):
				self.mime_type = getFileType(os.path.join(ANNEX_DIR, self.file_name))

			alias = self.getFileMetadata("uv_file_alias")
			if alias is not None:
				self.file_alias = alias
			
			self.save()
	
	def addCompletedTask(self, task_path):
		if not hasattr(self, "completed_tasks"):
			self.completed_tasks = []
		
		if task_path not in self.completed_tasks:
			self.completed_tasks.append(task_path)
			self.saveFields('completed_tasks')