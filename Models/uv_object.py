import os
from json import dumps
from subprocess import Popen, PIPE

from lib.Core.Models.uv_object import UnveillanceObject as UVO_Stub
from lib.Core.vars import EmitSentinel
from Models.uv_elasticsearch import UnveillanceElasticsearchHandler

from conf import ANNEX_DIR, DEBUG

class UnveillanceObject(UVO_Stub, UnveillanceElasticsearchHandler):
	def __init__(self, _id=None, inflate=None, emit_sentinels=None):
		UnveillanceElasticsearchHandler.__init__(self)
		
		if emit_sentinels is None: emit_sentinels = []
		emit_sentinels.extend([
			EmitSentinel("elasticsearch", "UnveillanceElasticsearch", None)])
		
		super(UnveillanceObject, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=emit_sentinels)
		
	def save(self):
		if DEBUG: print "SAVING AS ANNEX/WORKER OBJECT"
		if self.addFile(self.manifest, dumps(self.emit())):
			if DEBUG: print self.emit()
			return self.update(self._id, self.emit())
		
		return False
	
	def getObject(self, _id):
		try: self.inflate(self.get(_id))
		except Exception as e:
			if DEBUG: print e
			self.invalidate(error="Object does not exist in Elasticsearch")
	
		if DEBUG: print self.emit()
	
	def getFile(self, asset_path):
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		res = False
		try:
			p = Popen(['git', 'annex', 'unlock', asset_path])
			p.wait()
			res =  True
		except Exception as e: print e
		
		os.chdir(this_dir)
		return res
		
	def addFile(self, asset_path, data):
		"""
			git annex add [file]
		"""
		if not self.getFile(asset_path): return False
		
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		try:
			with open(os.path.join(ANNEX_DIR, asset_path), 'wb+') as file:
				file.write(data)

			p = Popen(['git', 'annex', 'add', asset_path])
			p.wait()
		except Exception as e:
			print e
			os.chdir(this_dir)
			return False
		
		try:
			p = Popen(['git', 'commit', asset_path, '-m', '"saved asset"'])
			p.wait()
		except Exception as e:
			print e
		
		os.chdir(this_dir)
		return True
			
	def addAsset(self, data, file_name, as_original=False, as_literal=True, **metadata):
		print "ADDING ASSET AS ANNEX/WORKER OBJECT"
		if not as_original: asset_path = os.path.join(self.base_path, file_name)
		else: asset_path = file_name			
		
		asset_path = super(UnveillanceObject, self).addAsset(data, file_name, asset_path,
			as_literal=as_literal, **metadata)
		
		if data is not None and asset_path:
			if not as_literal: data = dumps(data)
			if not self.addFile(asset_path, data): return False
			
		return asset_path