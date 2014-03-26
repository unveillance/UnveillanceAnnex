from json import dumps

from lib.Core.Models.uv_object import UnveillanceObject as UVO_Stub
from lib.Core.Utils.uv_elasticsearch import UnveillanceElasticsearch

class UnveillanceObject(UVO_Stub):
	def __init__(self, **args):
		super(UnveillanceObject, self).__init__(**args)
	
	def save(self):
		print "SAVING AS ANNEX/WORKER OBJECT"
		# TODO: HOW??
	
	def addAsset(self, data, file_name, as_literal=False, **metadata):
		print "ADDING ASSET AS ANNEX/WORKER OBJECT"
		if data is not None:
			if not as_literal:
				data = dumps(data)
			
			# TODO: WHAT TO DO WITH DATA???
			# SEND IT BACK TO ITS CONTEXT
			
		asset = {'file_name' : file_name}
		for k,v in metadata.iteritems():
			asset[k] = v
			print "metadata added: %s = %s" % (k, v)
		
		if not hasattr(self, "assets"):
			self.assets = []
		
		entry = [e for e in self.assets if e['file_name'] == asset['file_name']]
		if len(entry) == 1:
			entry[0].update(asset)
		else:
			self.assets.append(asset)

		self.save()
		return os.path.join(self.base_path, file_name)