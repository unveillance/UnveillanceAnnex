from lib.Worker.Models.uv_task import UnveillanceTask
from conf import DEBUG

class UnveillanceCluster(UnveillanceTask):
	def __init__(self, _id=None, inflate=None):	
		if inflate is not None:
			for must in ['documents', 'task_path']:
				if must not in inflate.keys():
					raise Exception("No documents and/or task_path")

			if DEBUG: print "INFLATING CLUSTER"
			
			from lib.Core.Utils.funcs import generateMD5Hash
			from conf import UUID

			inflate.update({
				'_id' : generateMD5Hash(content="".join(inflate['documents']), salt=inflate['task_path']),
				'queue' : UUID,
				'uv_cluster' : True
			})
			
		super(UnveillanceCluster, self).__init__(_id=_id, inflate=inflate)
	
	def inflate(self, inflate):
		super(UnveillanceCluster, self).inflate(inflate)

		if not hasattr(self, "built") or not self.built:
			self.run()