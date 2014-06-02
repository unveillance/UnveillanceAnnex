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
		
	def save(self):
		if DEBUG: print "SAVING AS ANNEX/WORKER OBJECT"
		return self.update(self._id, self.emit())
		
	def getObject(self, _id):
		try: self.inflate(self.get(_id))
		except Exception as e:
			if DEBUG: print "ERROR GETTING OBJECT: %s" % e
			self.invalidate(error="Object does not exist in Elasticsearch")
		
	def getFile(self, asset_path):
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		res = False
		try:
			p = Popen(['git', 'annex', 'unlock', asset_path])
			p.wait()
			res =  True
		except Exception as e: 
			print "COULD NOT GET FILE:"
			print e
		
		os.chdir(this_dir)
		return res
	
	def loadFile(self, asset_path):
		if self.getFile(asset_path):
			try:
				with open(os.path.join(ANNEX_DIR, asset_path), 'rb') as file:
					return file.read()
			except IOError as e:
				print "COULD NOT LOAD FILE:"
				print e
		
		return None
		
	def addFile(self, asset_path, data, sync=False):
		"""
			git annex add [file]
		"""
		#if not self.getFile(asset_path): return False
		
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		if data is not None:
			if DEBUG: print data
			try:
				with open(os.path.join(ANNEX_DIR, asset_path), 'wb+') as f: f.write(data)
			except Exception as e:
				print e
				os.chdir(this_dir)
				return False
		
		if sync:
			try:
				p = Popen(['git', 'annex', 'add', asset_path])
				p.wait()
			except Exception as e:
				print e
				os.chdir(this_dir)
				return False
		
			try:
				p = Popen(['git', 'commit', asset_path, '-m', '"saved and synced asset"'])
				p.wait()
			except Exception as e:
				print e
		
		os.chdir(this_dir)
		return True
			
	def addAsset(self, data, file_name, as_literal=True, **metadata):
		print "ADDING ASSET AS ANNEX/WORKER OBJECT"
		asset_path = os.path.join(self.base_path, file_name)
		
		asset_path = super(UnveillanceObject, self).addAsset(file_name, asset_path,
			as_literal=as_literal, **metadata)
		
		if data is not None and asset_path:
			print "HERE IS THE DATA I PLAN ON ADDING:"
			print data
			
			if not as_literal: data = dumps(data)
			if not self.addFile(asset_path, data): return False
			
		return asset_path