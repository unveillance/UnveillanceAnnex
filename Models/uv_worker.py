from __future__ import absolute_import

import os, sys
from time import sleep
from celery import Celery

from conf import MONITOR_ROOT, UUID, SERVER_HOST, DEBUG

from Utils.funcs import printAsLog
from lib.Core.Utils.funcs import startDaemon, stopDaemon

class UnveillanceWorker(object):
	def __init__(self):		
		self.worker_pid_file = os.path.join(MONITOR_ROOT, "worker.pid.txt")
		self.worker_log_file = os.path.join(MONITOR_ROOT, "worker.log.txt")
			
	def startWorker(self):
		printAsLog("STARTING CELERY WORKER!")

		from lib.Worker.vars import TASKS_ROOT, buildCeleryTaskList, ALL_WORKERS
		self.celery_tasks = buildCeleryTaskList()
		
		sys.argv.extend(['worker', '-l', 'info', '-Q', ",".join([ALL_WORKERS, UUID])])
		if DEBUG: print sys.argv
		
		#startDaemon(self.worker_log_file, self.worker_pid_file)
		
		#self.celery_app = Celery(TASKS_ROOT, 
		#	broker='amqp://guest@%s' % SERVER_HOST, include=self.celery_tasks)
		
		self.celery_app = Celery(TASKS_ROOT,
			broker='amqp://guest@localhost//', include=self.celery_tasks)

		#self.celery_app.start()
	
	def stopWorker(self):
		printAsLog("WORKER EXHAUSTED. FINISHING!")
		#stopDaemon(self.worker_pid_file)