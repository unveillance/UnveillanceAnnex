import os, re
from json import dumps
from copy import deepcopy
from subprocess import Popen, PIPE
from fabric.api import local, settings
from fabric.context_managers import hide

from lib.Core.Models.uv_object import UnveillanceObject as UVO_Stub
from lib.Core.vars import EmitSentinel
from Models.uv_elasticsearch import UnveillanceElasticsearchHandler

from conf import ANNEX_DIR, DEBUG, getSecrets

class UnveillanceObject(UVO_Stub, UnveillanceElasticsearchHandler):
	def __init__(self, _id=None, inflate=None, emit_sentinels=None):
		UnveillanceElasticsearchHandler.__init__(self)
		
		if emit_sentinels is None: emit_sentinels = []
		emit_sentinels.extend([
			EmitSentinel("elasticsearch", "UnveillanceElasticsearch", None),
			EmitSentinel("already_exists", "str", None)])
		
		if inflate is not None:
			if self.get(inflate['_id']) is not None:
				if DEBUG: 
					print "this object already exists. use it instead of re-creating it."

				_id = inflate['_id']
				self.already_exists = True
				inflate = None
		
		super(UnveillanceObject, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=emit_sentinels)
		
	def save(self, create=False):
		if DEBUG: 
			print "\n\n**SAVING AS ANNEX/WORKER OBJECT"
		
		if create:
			return self.create(self._id, self.emit())
		else:
			return self.update(self._id, self.emit())
	
	def saveFields(self, fields):
		if DEBUG:
			print "\n\n** UPDATE/SAVING ANNEX/WORKER OBJECT"
		
		if type(fields) is not list:
			fields = [fields]
		
		new_data = {}
		for field in fields:
			try:
				new_data[field] = getattr(self, field)
			except Exception as e:
				if DEBUG: print "could not update field %s" % field
				continue
		
		if len(new_data.keys()) == 0: return False
		
		return self.updateFields(self._id, new_data)
		
	def getObject(self, _id, els_doc_root=None):
		try: self.inflate(self.get(_id, els_doc_root=els_doc_root))
		except Exception as e:
			if DEBUG: print "ERROR GETTING OBJECT: %s" % e
			self.invalidate(error="Object does not exist in Elasticsearch")
		
	def getFile(self, asset_path):
		return self.queryFile(asset_path)
	
	def queryFile(self, asset_path):
		return os.path.exists(os.path.join(ANNEX_DIR, asset_path))
	
	def loadFile(self, asset_path):
		if self.getFile(asset_path):
			try:
				with open(os.path.join(ANNEX_DIR, asset_path), 'rb') as file:
					return file.read()
			except IOError as e:
				print "COULD NOT LOAD FILE:"
				print e
		
		return None

	def getFileMetadata(self, key):
		if hasattr(self, "uv_metadata") and key in self.uv_metadata.keys():
			return self.uv_metadata[key]

		return None

	def set_file_metadata(self, key, value):
		if not hasattr(self, "uv_metadata"):
			self.uv_metadata = {}

		try:
			self.uv_metadata[key] = value
			return self.save()
		except Exception as e:
			print e, type(e)

		return False
		
	def addFile(self, asset_path, data):
		if data is not None:
			try:
				# 4. write
				with open(os.path.join(ANNEX_DIR, asset_path), 'wb+') as f:
					f.write(data)
					return True
			except Exception as e:
				print "FAILED TO WRITE FILE, I D K WHY?"
				print e, type(e)

		# else touch? IDK

		return False
			
	def addAsset(self, data, file_name, as_literal=True, **metadata):
		print "ADDING ASSET AS ANNEX/WORKER OBJECT"
		asset_path = os.path.join(self.base_path, file_name)
		
		asset_path = super(UnveillanceObject, self).addAsset(file_name, asset_path,
			as_literal=as_literal, **metadata)
		
		if data is not None and asset_path:
			if not as_literal: data = dumps(data)
			if not self.addFile(asset_path, data):
				if DEBUG: print "COULD NOT ADD FILE."
				return False
			
		return asset_path