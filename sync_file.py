from sys import argv, exit

def sync_file(file_name, with_metadata=None):
	import requests
	
	from Utils.funcs import printAsLog
	from conf import HOST, API_PORT, DEBUG

	if with_metadata is not None:
		if DEBUG:
			print "FIRST METADATA:"
			print with_metadata

		if type(with_metadata) is list and len(with_metadata) > 0:
			with_metadata = dict(tuple([d.replace("--","") for d in m.split("=")]) for m in with_metadata if m[:2] == "--")

			if DEBUG:
				print "TRANSFORMED METADATA:"
				print with_metadata
	try:
		r = requests.post("http://%s:%d/sync/%s" % (HOST, API_PORT, file_name), data=with_metadata)
		return (r.status_code == 200)
	except Exception as e:
		printAsLog(e, as_error=True)

	return False

if __name__ == "__main__":	
	if sync_file(argv[1], with_metadata=argv[1:]):
		exit(0)
	
	exit(-1)
