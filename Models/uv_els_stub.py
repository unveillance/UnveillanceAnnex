__metaclass__ = type

import os, json
from collections import namedtuple
from copy import deepcopy
from time import time

from lib.Core.vars import EmitSentinel
from Models.uv_elasticsearch import UnveillanceElasticsearchHandler

from conf import DEBUG

EMIT_SENTINELS = [
		EmitSentinel("emit_sentinels", "EmitSentinel", None),
		EmitSentinel("els_doc_root", "str", None),
		EmitSentinel("invalid", "bool", None),
		EmitSentinel("errors", "list", None)]

class UnveillanceELSStub(UnveillanceElasticsearchHandler):
	def __init__(self, els_doc_root, emit_sentinels=None, _id=None, inflate=None):		
		self.emit_sentinels = deepcopy(EMIT_SENTINELS)
		self.els_doc_root = els_doc_root
		
		if emit_sentinels is not None:
			if type(emit_sentinels) is not list:
				emit_sentinels = [emit_sentinels]
			
			self.emit_sentinels.extend(emit_sentinels)
			
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash

			inflate['date_added'] = time() * 1000

			if '_id' not in inflate.keys():
				inflate['_id'] = generateMD5Hash(salt=inflate['date_added'])

			self.inflate(inflate)
			self.save(create=True)
		
		elif _id is not None: self.getObject(_id, els_doc_root)

	def getObject(self, _id, els_doc_root):
		try: self.inflate(self.get(_id, els_doc_root=els_doc_root))

		except Exception as e:
			if DEBUG: print "ERROR GETTING OBJECT: %s" % e

	def save(self, create=False):
		if DEBUG: 
			print "\n\n**SAVING AS ELS STUB"
		
		if create:
			return self.create(self._id, self.emit())
		else:
			return self.update(self._id, self.emit())

	def emit(self, remove=None):
		emit_ = deepcopy(self.__dict__)
		for e in [e for e in self.emit_sentinels if hasattr(self, e.attr)]:				
			if e.s_replace is None:
				del emit_[e.attr]
			else:
				rep = getattr(self, e.attr)			
				if type(rep) is list:
					emit_[e.attr] = []
					for r in rep:
						try:
							emit_[e.attr].append(getattr(r, e.s_replace))
						except Exception as ex:
							emit_[e.attr].append(r)

				else:
					emit_[e.attr] = getattr(rep, e.s_replace)
		
		if remove is not None:
			if type(remove) is not list:
				remove = [remove]
			
			for r in remove: del emit_[r]

		return emit_
	
	def invalidate(self, error=None):
		self.invalid = True
		if error is not None:
			if not hasattr(self, "errors"): self.errors = []
			self.errors.append(error)
	
	def inflate(self, attrs):
		for k,v in attrs.iteritems():
			setattr(self, k, v)