from Models.uv_object import UnveillanceObject
from vars import EmitSentinel
from conf import DEBUG

class UnveillanceText(UnveillanceObject):
	def __init__(self, _id=None, inflate=None, emit_sentinels=None):
		if emit_sentinels is None: emit_sentinels = []
		if type(emit_sentinels) is not list: emit_sentinels = [emit_sentinels]
		emit_sentinels.append(EmitSentinel("els_doc_root", "str", None))

		if inflate is not None:
			import os
			from fabric.api import settings, local
			
			from lib.Core.Utils.funcs import generateMD5Hash
			from conf import UUID, ANNEX_DIR
			from vars import UV_DOC_TYPE, MIME_TYPES
			
			inflate['_id'] = generateMD5Hash(content=inflate['media_id'], 
				salt=MIME_TYPES['txt_stub'])
			
			inflate['farm'] = UUID
			inflate['uv_doc_type'] = UV_DOC_TYPE['DOC']
			inflate['mime_type'] = MIME_TYPES['txt_stub']
			inflate['els_doc_root'] = "uv_text_stub"
			
			this_dir = os.getcwd()
			os.chdir(ANNEX_DIR)
			
			file_name = "%s_%s" % (inflate['media_id'],
				inflate['file_name'].split("/")[-1])
			
			with settings(warn_only=True):
				ln = local("ln -s %s %s" % (inflate['file_name'], file_name),
					capture=True)
				
				if DEBUG: print ln
			
			os.chdir(this_dir)
			inflate['file_name'] = file_name

		super(UnveillanceText, self).__init__(_id=_id, 
			inflate=inflate, emit_sentinels=emit_sentinels)

		if inflate is not None:
			if "searchable_text_type" in inflate.keys() and "searchable_text" in inflate.keys():
				from Models.uv_els_stub import UnveillanceELSStub

				for i, st in enumerate(inflate['searchable_text']):
					els_stub = UnveillanceELSStub(inflate['searchable_text_type'], inflate={
						'media_id' : inflate['_id'],
						'searchable_text' : st,
						'index_in_parent' : i
					})
	
	def inflate(self, attrs):
		attrs['els_doc_root'] = "uv_text_stub"
		if DEBUG: print "SETTING ELS DOC ROOT FOR THIS TYPE! ATTRS:\n%s" % attrs.keys()
		super(UnveillanceText, self).inflate(attrs)

	def getObject(self, _id, els_doc_root=None):
		if DEBUG: print "DIFFERENT getObject METHOD FOR THIS TYPE"
		super(UnveillanceText, self).getObject(_id, els_doc_root="uv_text_stub")

	