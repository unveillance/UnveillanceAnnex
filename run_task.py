from sys import argv, exit

def run_task(task_id):
	from Utils.funcs import printAsLog
	from lib.Worker.Models.uv_task import UnveillanceTask
	
	try:
		task = UnveillanceTask(_id=task_id)
	except Exception as e:
		printAsLog("no task id.  quitting", as_error=True)
		return False	

	import requests
	from conf import HOST, API_PORT
	
	try:
		r = requests.post("http://%s:%d/task/" % (HOST, API_PORT), 
			data={ '_id' : task._id })
	except Exception as e:
		printAsLog(e, as_error=True)
		return False

	return True

if __name__ == "__main__":
	if not run_task(argv[1]): exit(-1)
	exit(0)
