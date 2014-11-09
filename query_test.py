from sys import argv, exit

def iterate_query(els_handler, _scroll_id):
	from pprint import pprint
	from fabric.operations import prompt

	print "\n****** ITERATE OVER REST? (y or n) ******"
	print "*** SCROLL ID : %s ***\n\n" % _scroll_id
	
	iterate = False if prompt("[DEFAULT y]: ") == "n" else True

	if not iterate: return True

	res = els_handler.iterateOverScroll(_scroll_id)
	if res is not None:
		pprint(res)
		return iterate_query(els_handler, res['_scroll_id'])

	return True


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
			return False
	else:
		try:
			with open(args[0], 'rb') as q:
				query = loads(q.read())
		except Exception as e:
			print "No readable json found at %s" % args[0]
			print e
			return False

	if query is None: return False

	if query.keys()[0] == "query": query = query['query']

	from pprint import pprint
	from Models.uv_elasticsearch import UnveillanceElasticsearchHandler
	
	els = UnveillanceElasticsearchHandler()
	res = els.getScroll(query, doc_type="uv_document" if len(args) == 1 else args[1], exclude_fields=True)

	if res is None:
		print "NO RESULT."
		return False

	pprint(res)
	
	return iterate_query(els, res['_scroll_id'])

if __name__ == '__main__':
	if len(argv) < 2: exit(-1)
	
	if not test_query(argv[1:]): exit(-1)
	exit(0)
