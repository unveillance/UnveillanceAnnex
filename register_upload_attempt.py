from sys import argv, exit

def register_upload_attempt(_id):
	from Utils.funcs import printAsLog
	from lib.Worker.Models.uv_document import UnveillanceDocument

	try:
		doc = UnveillanceDocument(_id=_id)
		if doc.getFileMetadata('upload_attempts') == None:
			upload_attempts = 1
		else:
			upload_attempts += 1

		doc.set_file_metadata('upload_attempts', upload_attempts)
		
	except Exception as e:
		printAsLog(e, as_error=True)
		return False

	return True

if __name__ == "__main__":	
	if not register_upload_attempt(argv[1]):
		exit(-1)
	
	exit(0)
