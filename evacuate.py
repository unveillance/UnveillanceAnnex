from sys import exit

def evacuate(evac_root=None, omit_list=None):
	import os, re
	from copy import deepcopy
	from fabric.api import local, settings
	from fabric.context_managers import hide

	from Models.uv_elasticsearch import UnveillanceElasticsearchHandler
	from conf import ANNEX_DIR, getConfig
	from vars import CUSTOM_QUERIES

	els = UnveillanceElasticsearchHandler()

	evacuated = []
	if omit_list is not None:
		for _, _, files in os.walk(omit_list):
			omit_list = files
			break
	else: omit_list = []
	print omit_list

	with_documents = els.query(CUSTOM_QUERIES['GET_ALL_WITH_ATTACHMENTS'],
		doc_type="uv_document", exclude_fields=True)

	if with_documents is not None:
		for d in [d['documents'] for d in with_documents['documents']]:
			for document in d:
				try:
					omit = els.get(document, els_doc_root="uv_document")['file_name']
				except: pass

				omit_list.append(omit)

	os.chdir(ANNEX_DIR)
	for root, _, files in os.walk(ANNEX_DIR):
		for file in files:
			if file in omit_list:
				print "OMITTING %s" % file
				continue

			evacuated.append(file)
		break

	if len(evacuated) == 0:
		print "No files to evacuate."
		return None

	from json import dumps
	from Models.uv_object import UnveillanceObject
	from vars import GIT_ANNEX_METADATA
	
	if evac_root is None: evac_root = os.path.expanduser("~")

	evac_root = os.path.join(evac_root, "UNVEILLANCE_MEDIA_EVACUATED")
	GIT_ANNEX = os.path.join(getConfig('git_annex_bin'), "git-annex")

	if os.path.exists(evac_root):
		with settings(warn_only=True):
			local("rm -rf %s" % evac_root)

	cmd = "mkdir -p %s" % evac_root
	with settings(warn_only=True): local(cmd)

	manifest = []

	for file in evacuated:
		# get file from elasticsearch
		d_query = deepcopy(CUSTOM_QUERIES['GET_BY_FILE_NAME'])
		d_query['bool']['must'][0]['match']['uv_document.file_name'] = file
		print d_query

		documents = els.query(d_query, doc_type="uv_document", exclude_fields=True)
		if documents is not None:
			for document in [UnveillanceObject(_id=d['_id']) for d in documents['documents']]:
				dm = { 'file_name' : file }
				for f in GIT_ANNEX_METADATA:
					facet = document.getFileMetadata(f)
					if facet is not None: dm[f] = facet
				
				manifest.append(dm)

		for cmd in [
			"%(ga)s add %(f)s && %(ga)s unlock %(f)s" % ({ 'ga' : GIT_ANNEX, 'f' : file }),
			"cp %s %s" % (file, evac_root)]:
			with settings(hide('everything'), warn_only=True): local(cmd)

	with open(os.path.join(evac_root, "evac_manifest.json"), 'wb+') as m: m.write(dumps(manifest))
	cmd = "tar -cvzf %(e)s.tar.gz %(e)s" % ({ 'e' : evac_root})
	with settings(warn_only=True): local(cmd)
	
	print "\n***************************"
	print "%(l)d files evacuated and can be found at %(e)s (tarred at %(e)s.tar.gz)" % ({'l' : len(evacuated), 'e' : evac_root })
	return (evac_root, "%s.tar.gz" % evac_root)

if __name__ == "__main__":
	if evacuate() is None: exit(-1)
	exit(0)