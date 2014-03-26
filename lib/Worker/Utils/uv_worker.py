from __future__ import absolute_import

import os, sys
from time import sleep
from celery import Celery

from conf import MONITOR_ROOT, UUID

from Utils.funcs import printAsLog
from lib.Core.Utils.funcs import startDaemon, stopDaemon

class UnveillanceWorker():
	def __init__(self):		
		self.worker_pid_file = os.path.join(MONITOR_ROOT, "worker.pid.txt")
		self.worker_log_file = os.path.join(MONITOR_ROOT, "worker.log.txt")
			
	def setTask(self, task):
		printAsLog("SETTING TASK")
		print dir(self)
		task.ctx = self
		
		print task.emit()
		print dir(task.ctx)
	
	def startWorker(self):
		printAsLog("STARTING CELERY WORKER!")

		from lib.Worker.vars import TASKS_ROOT, buildCeleryTaskList, ALL_WORKERS
		celery_tasks = buildCeleryTaskList()
		
		
		sys.argv.extend(['worker', '-l', 'info', '-Q', ",".join([ALL_WORKERS, UUID])])
		print sys.argv
		
		startDaemon(self.worker_log_file, self.worker_pid_file)
		self.celery_app = Celery(TASKS_ROOT, broker='amqp://', 
			backend='amqp://', include=celery_tasks)
		
		self.celery_app.start()
	
	def stopWorker(self):
		printAsLog("WORKER EXHAUSTED. FINISHING!")
		stopDaemon(self.worker_pid_file)