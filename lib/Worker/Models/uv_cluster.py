from Models.uv_object import UnveillanceObject
from conf import DEBUG
from vars import ASSET_TAGS

class UnveillanceCluster(UnveillanceObject):
	def __init__(self, _id=None, inflate=None):
	
		if inflate is not None:
			print "INFLATING CLUSTER"
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash(content="".join(inflate['documents']),
				salt=inflate['asset_tag'])
			
		super(UnveillanceCluster, self).__init__(_id=_id, inflate=inflate)			
	
	def inflate(self, inflate):
		super(UnveillanceCluster, self).inflate(inflate)
		if not hasattr(self, "already_exists") or not self.already_exists: self.build()
	
	def build(self):
		"""
			get all those assets and burn them to a csv or json document
		"""
		if DEBUG: print "BUILDING CLUSTER"
		
		from lib.Worker.Models.uv_document import UnveillanceDocument
		from cStringIO import StringIO
		import csv, json
		
		whole_cluster = StringIO()
		cluster_type = "csv"
		
		for d, doc in enumerate(self.documents):
			doc = UnveillanceDocument(_id=doc)
			if doc is None: continue
			
			try:
				cluster_doc = doc.getAssetsByTagName(self.asset_tag)[0]
			except IndexError as e: 
				if DEBUG: print "Could not get cluster doc: %s" % e
				continue
			
			content = doc.loadAsset(cluster_doc['file_name'])
			if content is None:
				if DEBUG: print "Cluster doc has no content"
				continue
			
			if DEBUG: print content
			if cluster_type == "csv":
				for r, row in enumerate(content.splitlines()):
					# if idx == 0, we can include the labels
					if DEBUG: print row
					
					if r == 0 and d != 0: continue
					whole_cluster.write(row + "\n")
					
			elif cluster_type == "json": continue
		
		
		asset = self.addAsset(whole_cluster.getvalue(), "cluster_data.%s" % cluster_type,
			tags=[ASSET_TAGS["F_MD"]],
			description="%s aggregation of all cluster data" % cluster_type)
		
		whole_cluster.close()
		if asset is not None: addFile(self, asset, None, sync=True)