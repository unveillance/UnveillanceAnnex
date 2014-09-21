from sys import argv, exit

def test_query(args):
	import os
	from json import loads

	query = None

	if args[0][0] == "{":
		try:
			query = loads(args[0])
		except Exception as e:
			print "Not a dict at all."
			print e
			return None
	else:
		try:
			with open(args[0], 'rb') as q:
				query = loads(q.read())
		except Exception as e:
			print "No readable json found at %s" % args[0]
			print e
			return None

	if query is None: return None

	from pprint import pprint
	from Models.uv_elasticsearch import UnveillanceElasticsearchHandler
	
	els = UnveillanceElasticsearchHandler()
	res = els.query(query, doc_type="uv_document" if len(args) == 1 else args[1])

	pprint(res)
	return res

if __name__ == '__main__':
	if len(argv) < 2: exit(-1)
	
	if test_query(argv[1:]) is None: exit(-1)
	exit(0)
