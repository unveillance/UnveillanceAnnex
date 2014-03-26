import sys, pkgutil
from collections import namedtuple
from inspect import getmembers, ismodule, isfunction
from celery import Celery

MAX_PAGES = 300
TASKS_ROOT = "lib.Worker.Tasks"
CELERY_TASKS = None
CELERY_STUB = Celery(None, broker='amqp://', backend='amqp://')
ALL_WORKERS = "all_workers"

mime_types = namedtuple("mime_types", "PDF TEXT IMAGE VIDEO EVALUATE")
MimeTypes = mime_types(
	"application/pdf", "plain/txt", 
	"image/jpeg", "video/x-matroska", 
	["application/pdf", "plain/txt", 
		"image/jpeg", "video/x-matroska"])

resolutions = namedtuple("resolutions", "LOW MED HIGH THUMB")
Resolutions = resolutions([0.5, 0.5], [0.75, 0.75], [1, 1], [0.15, 0.15])

asset_tags = namedtuple("asset_tags", "ORIG TXT_E TXT_O TXT_P BOW KW DOC_SPLIT F_MD")
AssetTags = asset_tags("original_document", "embedded_text", "ocr_text", "prefered_text",
	"bag_of_words", "keywords", "doc_split", "metadata_fingerprint")

peepdf_marker = namedtuple("peepdf_markers", "regex marker_name marker_label callback")
PeepDFMarkers = [peepdf_marker(r"^File:\s*(.*)", "file_name", "Filename", None),
	peepdf_marker(r"^SHA1:\s*(\w{40})", "sha1", "SHA1", None),
	peepdf_marker(r"^Size:\s*(\d+)\sbytes", "file_size", "File Size", None),
	peepdf_marker(r"^Version:\s*(.*)", "pdf_version", "PDF Version", None),
	peepdf_marker(r"/Title (.*)", "xmp_title", "XMP Title", None),
	peepdf_marker(r"/Creator (.*)", "xmp_creator", "XMP Creator", None),
	peepdf_marker(r"/ModDate D:(.*)'00", "xmp_mod_date", "XMP ModDate", None),
	peepdf_marker(r"/CreationDate(.*)", "xmp_creation_date", "XMP CreationDate", None),
	peepdf_marker(r"/Author (.*)", "xmp_author", "XMP Author", None),
	peepdf_marker(r"Object (\d+) in version (\d+):", "xmp_metadata_block",
		"XMP Metadata Block", "pullXMPMetadataBlock")]

def buildCeleryTaskList():
	CELERY_TASKS = []	
	
	__import__(TASKS_ROOT)
	for mod in [(n, t) for n, t in getmembers(sys.modules[TASKS_ROOT], ismodule)]:
		mod_name = "%s.%s" % (TASKS_ROOT, mod[0])
		
		try:
			for submod in [n for _, n, _ in pkgutil.iter_modules([mod[1].__path__[0]])]:
				submod = "%s.%s" % (mod_name, submod)
				pkg = __import__(submod)
				for func in [(n, t) for n, t in getmembers(sys.modules[submod])]:
					try:
						has_stack = func[1].__class__.__dict__['request_stack']
						if has_stack.__class__.__name__ == "_LocalStack":
							CELERY_TASKS.append(submod)
							break
					except: pass
		except AttributeError as e: pass
	
	return CELERY_TASKS