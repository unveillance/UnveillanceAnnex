from sys import argv, exit

def sync_file(file, with_metadata=None):
	import requests
	
	from Utils.funcs import printAsLog
	from conf import HOST, API_PORT

	if with_metadata is not None:
		if type(with_metadata) is list and len(with_metadata) > 0:
			with_metadata = dict(tuple([d.replace("--","") for d in m.split("=")]) for m in with_metadata if m[:2] == "--")

			print with_metadata

	try:
		r = requests.post("http://%s:%d/sync/%s" % (HOST, API_PORT, file), data=with_metadata)
		return (r.status_code == 200)
	except Exception as e:
		printAsLog(e, as_error=True)

	return False

if __name__ == "__main__":	
	if sync_file(argv[1], with_metadata=argv[1:]):
		exit(0)
	
	exit(-1)
