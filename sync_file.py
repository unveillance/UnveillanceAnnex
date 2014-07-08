import os, requests
from sys import argv, exit

if __name__ == "__main__":
	from Utils.funcs import printAsLog
	from conf import HOST, API_PORT
	
	try:
		r = requests.post("http://%s:%d/sync/%s" % (HOST, API_PORT, argv[1]))
	except Exception as e:
		printAsLog(e, as_error=True)
		exit(1)
	
	exit(0)
