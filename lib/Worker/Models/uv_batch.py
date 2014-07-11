from Models.uv_object import UnveillanceObject
from vars import EmitSentinel

class UnveillanceBatch(UnveillanceObject):
	def __init__(self, _id=None, inflate=None, emit_sentinels=None):
		EMIT_SENTINELS = [EmitSentinel("documents", "UnveillanceDocument", "_id")]
		
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			try:
				inflate['_id'] = generateMD5Hash(content="".join(inflate['documents']))
				print "NEW BATCH WITH ID %s" % inflate['_id']
				print inflate['documents']
			except Exception as e:
				print "ERROR WITH NEW BATCH ID GEN:"
				print e
		
		if emit_sentinels is None:
			if type(emit_sentinels) is not list:
				emit_sentinels = [emit_sentinels]

			EMIT_SENTINELS.extend(emit_sentinels)
		
		super(UnveillanceBatch, self).__init__(_id=_id, 
			inflate=inflate, emit_sentinels=EMIT_SENTINELS)