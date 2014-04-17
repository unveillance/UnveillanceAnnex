import magic, gzip
from cStringIO import StringIO

def getFileType(file, as_buffer=False):
	m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
	try:
		if not as_buffer:
			mime_type = m.id_filename(file)
		else:
			mime_type = m.id_buffer(file)

		m.close()
		return mime_type
		
	except: pass
	m.close()
	return None

def unGzipBinary(bin):
	try:
		with gzip.GzipFile(fileobj=StringIO(bin)) as G:
			return G.read()
			
	except Exception as e:
		return None

def unGzipFile(path):
	try:
		with gzip.GzipFile(path, 'rb') as G:
			return G.read()
			
	except Exception as e:
		return None