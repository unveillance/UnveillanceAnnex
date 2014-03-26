from hashlib import md5
import magic

def hashEntireFile(path_to_file):
	try:
		m = md5()
		with open(path_to_file, 'rb') as f:
			for chunk in iter(lambda: f.read(4096), b''):
				m.update(chunk)
		return m.hexdigest()
	
	except: pass
	return None

def getFileType(path_to_file):
	m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
	try:
		mime_type = m.id_filename(path_to_file)
		m.close()
		return mime_type
		
	except: pass
	m.close()
	return None