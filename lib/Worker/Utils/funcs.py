import magic

def getFileType(path_to_file):
	m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
	try:
		mime_type = m.id_filename(path_to_file)
		m.close()
		return mime_type
		
	except: pass
	m.close()
	return None