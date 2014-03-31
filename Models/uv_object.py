import os
from json import dumps
from subprocess import Popen, PIPE

from lib.Core.Models.uv_object import UnveillanceObject as UVO_Stub
from lib.Core.Utils.uv_elasticsearch import UnveillanceElasticsearch
from conf import ANNEX_DIR

class UnveillanceObject(UVO_Stub):
	def __init__(self, **args):
		emit_sentinels = [EmitSentinel("elasticsearch", "UnveillanceElasticsearch", None)]
		
		self.elasticsearch = UnveillanceElasticsearch()
		
		if inflate is not None:
			try:
				base_path = os.path.join(".data", inflate['_id'])
			except KeyError as e: return
			
			if not os.path.exists(os.path.join(ANNEX_DIR, base_path)):
				os.makedirs(os.path.join(ANNEX_DIR, base_path))
			
			inflate['base_path'] = base_path

		super(UnveillanceObject, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=emit_sentinels)
	
	def save(self):
		print "SAVING AS ANNEX/WORKER OBJECT"
		self.elasticsearch.update(self._id, self.emit())
	
	def addFile(self, asset_path, data):
		"""
			git annex add [file]
		"""
		try:
			with open(os.path.join(ANNEX_DIR, asset_path), 'wb+') as file:
				file.write(data)

			this_dir = os.getcwd()
			os.chdir(ANNEX_DIR)
			
			p = Popen(['git', 'annex', 'add', asset_path])
			p.wait()
			
			os.chdir(this_dir)
			
			return True
				
		except Exception as e: print e

		return False
	
	def addAsset(self, data, file_name, as_original=False, as_literal=True, **metadata):
		print "ADDING ASSET AS ANNEX/WORKER OBJECT"
		if not as_original: asset_path = os.path.join(self.base_path, file_name)
		else: asset_path = file_name
		
		if data is not None:
			if not as_literal: data = dumps(data)
			if not self.addFile(asset_path, data): return None
							
		asset = { 'file_name' : file_name }
		for k,v in metadata.iteritems():
			asset[k] = v
			print "metadata added: %s = %s" % (k, v)
		
		if not hasattr(self, "assets"): self.assets = []
		
		entry = [e for e in self.assets if e['file_name'] == asset['file_name']]
		if len(entry) == 1: entry[0].update(asset)
		else: self.assets.append(asset)

		self.save()
		return asset_path