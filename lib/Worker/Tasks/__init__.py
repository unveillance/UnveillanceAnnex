from importlib import import_module
import os

from conf import BASE_DIR, DEBUG
from vars import TASKS_ROOT

for _, dir, _ in os.walk(os.path.join(BASE_DIR, *TASKS_ROOT.split("."))):
	if len(dir) == 0: pass
	for mod in dir:
		if DEBUG: print "IMPORTING %s.%s" % (TASKS_ROOT, mod)
		import_module("%s.%s" % (TASKS_ROOT, mod))