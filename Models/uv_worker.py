from __future__ import absolute_import

import os, sys, signal, logging
from time import sleep

from celery import Celery
import sockjs.tornado
import tornado.ioloop
import tornado.web

from conf import MONITOR_ROOT, UUID, SERVER_HOST, TASK_CHANNEL_PORT, DEBUG

from Utils.funcs import printAsLog
from lib.Core.Utils.funcs import startDaemon, stopDaemon

def terminationHandler(signal, frame): exit(0)
signal.signal(signal.SIGINT, terminationHandler)

class TaskChannel(sockjs.tornado.SockJSConnection):
	clients = set()

	def on_open(self, info):
		if DEBUG:
			print "on_open"
			print type(self.session)

		self.clients.add(self)

		for c in self.clients:
			print c.session

		self.broadcast(self.clients, "OK")

	def on_close(self):
		if DEBUG: print "on_close"

		self.clients.remove(self)
		self.broadcast(self.clients, "goodbye")

	def on_message(self, message):
		if DEBUG: print message
		self.broadcast(self.clients, message)

	class InfoHandler(tornado.web.RequestHandler):
		def get(self): self.finish({ 'status' : 'OK' })

class UnveillanceWorker(object):
	def __init__(self):		
		self.worker_pid_file = os.path.join(MONITOR_ROOT, "worker.pid.txt")
		self.worker_log_file = os.path.join(MONITOR_ROOT, "worker.log.txt")

	
	def startWorker(self):
		printAsLog("STARTING CELERY WORKER!")

		from lib.Worker.vars import TASKS_ROOT, buildCeleryTaskList, ALL_WORKERS
		self.celery_tasks = buildCeleryTaskList()
		
		sys.argv.extend(['worker', '-l', 'info', '-Q', ",".join([ALL_WORKERS, UUID])])
		
		self.celery_app = Celery(TASKS_ROOT,
			broker='amqp://guest@localhost//', include=self.celery_tasks)
		
		startDaemon(self.worker_log_file, self.worker_pid_file)
		logging.getLogger().setLevel(logging.DEBUG)

		self.task_channel = sockjs.tornado.SockJSRouter(TaskChannel, '/(?:[a-z0-9]{32})')
		tc = tornado.web.Application(
			[(r'/info', TaskChannel.InfoHandler)] + self.task_channel.urls)
		tc.listen(TASK_CHANNEL_PORT, no_keep_alive=True)

		if DEBUG: print "TaskChannel started on port %d" % TASK_CHANNEL_PORT		
		tornado.ioloop.IOLoop.instance().start()

	def stopWorker(self):
		printAsLog("WORKER EXHAUSTED. FINISHING!")
		stopDaemon(self.worker_pid_file)