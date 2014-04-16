from Models.uv_object import UnveillanceObject
from conf import DEBUG

class UnveillanceCluster(UnveillanceObject):
	def __init__(self, _id=None, inflate=None):
	
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash(content="".join(inflate['documents']),
				salt=inflate['asset_tag'])
			
		super(UnveillanceObject, self).__init__(_id=_id, inflate=inflate)
		
		if inflate is not None: self.build()
	
	def build(self):
		"""
			get all those assets and burn them to a csv or json document
		"""
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
			
			"""
				what type of cluster are we creating?
				csv? json array? some other type?
			"""
			if cluster_type == "csv":
				try:
					content_csv = csv.reader(content)
					for r, row in content_csv:
						# if idx == 0, we can include the labels
						if r == 0 and d != 0: continue
						whole_cluster.write(row)
				except ValueError as e:
					if DEBUG: print e
					continue
					
			elif cluster_type == "jarray": continue