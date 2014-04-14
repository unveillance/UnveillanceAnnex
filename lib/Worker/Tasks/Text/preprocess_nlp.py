from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessNLP(task):
	print "\n\n************** TEXT NLP PREPROCESSING [START] ******************\n"
	print "nlp preprocessing text at %s" % task.doc_id
	task.setStatus(412)
	
	import re
	from json import loads
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from lib.Core.Utils.funcs import cleanAndSplitLine
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	document = UnveillanceDocument(_id=task.doc_id)
	if document is None: 
		print "DOC IS NONE"
		return
		
	#	1. get all the words (bag of words)
	try:
		texts = loads(document.loadAsset("doc_texts.json"))
		if DEBUG: print "TEXTS:%s" % texts
	except Exception as e:
		print "ERROR GETTING DOC-TEXTS: %s" % e
		print "\n\n************** TEXT NLP PREPROCESSING [ERROR] ******************\n"
		return
	
	word_groups = [cleanAndSplitLine(text) for text in texts]
	word_groups = [wg for wg in word_groups if len(wg) > 0]
	bag_of_words = sum(word_groups, [])
	document.addAsset(bag_of_words, "bag_of_words.txt", as_literal=False,
		description="bag of words", tags=ASSET_TAGS['BOW'])
	
	#	2. get keywords, weighted and parsable by gensim
	once_words = set(word for word in set(bag_of_words) if bag_of_words.count(word) == 1)
	key_words = [word for word in bag_of_words if word not in once_words]
	
	if len(key_words) > 0:	
		document.addAsset(key_words, "key_words_gensim.txt", as_literal=False,
			description="keywords, as list, and parsable by gensim",
			tags=ASSET_TAGS['KW'])

	task.finish()
	print "\n\n************** TEXT NLP PREPROCESSING [END] ******************\n"