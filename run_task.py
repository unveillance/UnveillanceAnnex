import os, requests
from sys import argv, exit

if __name__ == "__main__":
	from Utils.funcs import printAsLog
	from lib.Worker.Models.uv_task import UnveillanceTask
	
	try:
		task = UnveillanceTask(_id=argv[1])
	except Exception as e:
		printAsLog("no task id.  quitting", as_error=True)
		exit(1)	

	from conf import HOST, API_PORT
	try:
		r = requests.post("http://%s:%d/task/" % (HOST, API_PORT), 
			data={ '_id' : task._id })
	except Exception as e:
		printAsLog(e, as_error=True)
		exit(1)
	
	exit(0)
