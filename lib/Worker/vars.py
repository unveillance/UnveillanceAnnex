import sys, pkgutil, os
from collections import namedtuple
from inspect import getmembers, ismodule, isfunction
from celery import Celery

from lib.Core.vars import MIME_TYPE_TASKS
from conf import BASE_DIR

MAX_PAGES = 300
TASKS_ROOT = "lib.Worker.Tasks"
CELERY_TASKS = None
CELERY_STUB = Celery(None, broker='amqp://', backend='amqp://')
ALL_WORKERS = "all_workers"

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