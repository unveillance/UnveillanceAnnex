from Models.uv_object import UnveillanceObject
from lib.Worker.Models.uv_batch import UnveillanceBatch
from conf import DEBUG
from vars import ASSET_TAGS, EmitSentinel

class UnveillanceCluster(UnveillanceObject):
	def __init__(self, _id=None, inflate=None):
	
		if inflate is not None:
			if DEBUG: print "INFLATING CLUSTER"
			from lib.Core.Utils.funcs import generateMD5Hash
			
			batch = UnveillanceBatch(_id="".join(inflate['documents']))
			if batch is None:
				batch = UnveillanceBatch(inflate={'documents' : inflate['documents']})
			
			if batch is None:
				if DEBUG: print "I CAN'T START UP THIS CLUSTER!"
				self.invalid = True
				return
			
			del inflate['documents']
			inflate.update({
				'batch' : batch._id,
				'_id' : generateMD5Hash(content=batch._id, salt=inflate['asset_tag'])
			})
			
		super(UnveillanceCluster, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=[EmitSentinel("batch", UnveillanceBatch, "_id")])
	
	def inflate(self, inflate):
		super(UnveillanceCluster, self).inflate(inflate)
		if not hasattr(self, "already_exists") or not self.already_exists: self.build()
		
		self.batch = UnveillanceBatch(_id=self.batch)
	
	def build(self):
		"""
			get all those assets and burn them to a csv or json document
		"""
		if DEBUG: print "BUILDING CLUSTER"
		
		from cStringIO import StringIO
		import csv, json
		
		whole_cluster = StringIO()
		cluster_type = "csv"
		
		for d, doc in enumerate(self.batch.documents):
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
		if asset is not None: self.addFile(asset, None, sync=True)