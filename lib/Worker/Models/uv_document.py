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
				
			self.mime_type = self.query_mime_type()

			alias = self.getFileMetadata("uv_file_alias")
			if alias is not None:
				self.file_alias = alias
			
			self.save()

	def set_import_count(self):
		times_imported = self.getFileMetadata("uv_import_count")
		if times_imported is None:
			times_imported = 0
		else:
			times_imported = int(times_imported)
		
		times_imported += 1
		self.set_file_metadata("uv_import_count", times_imported)

		return times_imported

	def query_mime_type(self):
		import os

		from lib.Worker.Utils.funcs import getFileType
		from conf import ANNEX_DIR
		
		mime_type = getFileType(os.path.join(ANNEX_DIR, self.file_name))
		
		if mime_type == "inode/symlink" and self.getFile(self.file_name):
			mime_type = getFileType(os.path.join(ANNEX_DIR, self.file_name))

		return mime_type
	
	def addCompletedTask(self, task_path):
		if not hasattr(self, "completed_tasks"):
			self.completed_tasks = []
		
		if task_path not in self.completed_tasks:
			self.completed_tasks.append(task_path)
			self.saveFields('completed_tasks')