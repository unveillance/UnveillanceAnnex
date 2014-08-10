import os, re
from json import dumps
from copy import deepcopy
from subprocess import Popen, PIPE
from fabric.api import local, settings
from fabric.context_managers import hide

from lib.Core.Models.uv_object import UnveillanceObject as UVO_Stub
from lib.Core.vars import EmitSentinel
from Models.uv_elasticsearch import UnveillanceElasticsearchHandler

from conf import ANNEX_DIR, DEBUG, getSecrets

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
		if DEBUG: 
			print "\n\n**SAVING AS ANNEX/WORKER OBJECT"
		
		return self.update(self._id, self.emit())
	
	def saveFields(self, fields):
		if DEBUG:
			print "\n\n** UPDATE/SAVING ANNEX/WORKER OBJECT"
		
		if type(fields) is not list:
			fields = [fields]
		
		new_data = {}
		for field in fields:
			try:
				new_data[field] = getattr(self, field)
			except Exception as e:
				if DEBUG: print "could not update field %s" % field
				continue
		
		if len(new_data.keys()) == 0: return False
		
		if DEBUG: print "update: %s" % new_data
		return self.updateFields(self._id, new_data)

	def notarizedSave(self, fields):
		if DEBUG:
			print "\n\n** NOTARIZED SAVING ANNEX/WORKER OBJECT"

		# if annex does not have a gpg key to work with, saveFields
		try:
			gpg_dir = getSecrets('gpg_dir')
			gpg_pwd = getSecrets('gpg_pwd')
		except Exception as e:
			if DEBUG: print "cannot notarize: no %s" % e
			return self.saveFields(fields)

		for req in [gpg_dir, gpg_pwd]:
			if req is None:
				if DEBUG: print "cannot notarize: no GPG keys!"
				return self.saveFields(fields)

		if type(fields) is not list:
			fields = [fields]

		for field in fields:
			try:
				notarized = getattr(self, field)
			except Exception as e:
				if DEBUG: print "could not notarize %s" % field
				continue

			# get clearsign from gpg (with fabric)

			# stick it into notarized_data field
			if not hasattr(self, 'notarized_data'):
				self.notarized_data = {}

			self.notarized_data[field] = notarized

		del gpg_pwd
		del gpg_dir
		fields.append('notarized_data')

		return self.saveFields(self._id, fields)
		
	def getObject(self, _id):
		try: self.inflate(self.get(_id))
		except Exception as e:
			if DEBUG: print "ERROR GETTING OBJECT: %s" % e
			self.invalidate(error="Object does not exist in Elasticsearch")
		
	def getFile(self, asset_path):
		res = False
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		with settings(hide('everything'), warn_only=True):
			ga_unlock = local("git annex unlock %s" % asset_path)
		
		if DEBUG: print "unlocking asset %s:\n%s\n" % (asset_path, ga_unlock)
		
		for line in ga_unlock.splitlines():
			if re.match(r'add (?:.*) ok', line):
				if DEBUG: print "...AND SUCCEEDED...\n"
				res = True
				break
		
		if not res:
			res = self.queryFile(asset_path)
		
		os.chdir(this_dir)
		return res
	
	def queryFile(self, asset_path):
		res = False
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		with settings(hide('everything'), warn_only=True):
			ga_find = local("git annex find %s" % asset_path, capture=True)
			if ga_find == asset_path: res = True
			else:
				ga_query = local("git annex status", capture=True)
				
				for line in ga_query.splitlines():
					r = re.match(re.compile("(.{1,2}) %s" % asset_path), line)
					if r is not None:
						if DEBUG:
							print (line, r)
							print "...AND SUCCEEDED...\n"
						res = True
						break
		
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

	def getFileMetadata(self, key):
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)

		metadata = None

		with settings(warn_only=True):
			metadata = local("git annex metadata %s --json --get=%s"  % self.file_name, capture=True)
			if metadata == "": metadata = None

		os.chdir(this_dir)
		return metadata
		
	def addFile(self, asset_path, data, sync=False):
		"""
			git annex add [file]
		"""
		#if not self.getFile(asset_path): return False
		
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		
		if data is not None:
			# 1. file exists? git annex find
			# 2. if so, check out "git annex get asset_path"
			with settings(hide('everything'), warn_only=True):
				ga_find = local("git annex find %s" % asset_path, capture=True)
			
			if DEBUG: print "finding %s:\n%s\n" % (asset_path, ga_find)
			 
			for line in ga_find.splitlines():
				if line == asset_path:
					# 3. if it was already added, sync=True
					sync = True
					local("git annex unlock %s" % asset_path)
					break

			try:
				# 4. write
				with open(os.path.join(ANNEX_DIR, asset_path), 'wb+') as f: f.write(data)
			except Exception as e:
				print "FAILED TO WRITE FILE, I D K WHY?"
				print e
				os.chdir(this_dir)
				return False
		
		if sync:
			with settings(hide('everything'), warn_only=True):
				ga_add = local("git annex add %s" % asset_path, capture=True)
				ga_commit = local("git commit %s -m \"saved and synced asset\"",
					capture=True)

			if DEBUG: 
				print "adding asset back: %s\n%s" % (asset_path, ga_add)
				print "committing to git: %s\n" % ga_commit
			
		os.chdir(this_dir)
		return True
			
	def addAsset(self, data, file_name, as_literal=True, **metadata):
		print "ADDING ASSET AS ANNEX/WORKER OBJECT"
		asset_path = os.path.join(self.base_path, file_name)
		
		asset_path = super(UnveillanceObject, self).addAsset(file_name, asset_path,
			as_literal=as_literal, **metadata)
		
		if data is not None and asset_path:
			if DEBUG:
				print "HERE IS THE DATA I PLAN ON ADDING:"
				print type(data)
			
			if not as_literal: data = dumps(data)
			if not self.addFile(asset_path, data):
				if DEBUG: print "COULD NOT ADD FILE."
				return False
			
		return asset_path