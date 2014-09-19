import requests
from sys import argv, exit

def sync_file(file):
	from Utils.funcs import printAsLog
	from conf import HOST, API_PORT

	try:
		r = requests.post("http://%s:%d/sync/%s" % (HOST, API_PORT, file))
	except Exception as e:
		printAsLog(e, as_error=True)
		return False

	return True

if __name__ == "__main__":	
	if not sync_file(argv[1]): exit(-1)
	exit(0)
