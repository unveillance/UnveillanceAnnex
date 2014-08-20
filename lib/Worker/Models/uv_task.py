import os, requests
from crontab import CronTab
from time import sleep
from importlib import import_module
from multiprocessing import Process
from fabric.api import local, settings

from Models.uv_object import UnveillanceObject
from Utils.funcs import printAsLog
from lib.Core.Utils.funcs import stopDaemon, startDaemon

from vars import EmitSentinel, UV_DOC_TYPE, TASKS_ROOT
from conf import DEBUG, BASE_DIR, ANNEX_DIR, HOST, API_PORT, MONITOR_ROOT

class UnveillanceTask(UnveillanceObject):
	def __init__(self, inflate=None, _id=None):		
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			inflate['_id'] = generateMD5Hash()
			inflate['uv_doc_type'] = UV_DOC_TYPE['TASK']
			inflate['status'] = 404
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, 
			emit_sentinels=[EmitSentinel("ctx", "Worker", None)])

		self.pid_file = os.path.join(ANNEX_DIR, self.base_path, "pid.txt")
		self.log_file = os.path.join(ANNEX_DIR, self.base_path, "log.txt")
	
	def routeNext(self, inflate=None):
		if DEBUG: print "ROUTING NEXT TASK FROM QUEUE\nCLONING SOME VARS FROM SELF:\n%s" % self.emit()
		
		if hasattr(self, "no_continue"):
			if DEBUG: print "NO CONTINUE FLAG DETECTED.  NO ROUTING POSSIBLE."
			return
		
		if not hasattr(self, "task_queue"):
			if DEBUG: print "TASK HAS NO TASK QUEUE. NO ROUTING POSSIBLE."
			return
		
		if inflate is None: inflate = {}
		task_index = self.task_queue.index(self.task_path) + 1
		
		try:
			inflate['task_path'] = self.task_queue[task_index]
			print "TASK %s AT INDEX %d" % (inflate['task_path'], task_index)
		except Exception as e:
			if DEBUG: print "TASK QUEUE EXHAUSTED. NO ROUTING POSSIBLE.\n%s" % e
			return
		
		for a in ["doc_id", "queue", "task_queue"]:
			if hasattr(self, a):
				inflate[a] = getattr(self, a)
		
		next_task = UnveillanceTask(inflate=inflate)
		next_task.run()
		
	def run(self):
		if DEBUG: print "NOW RUNNING TASK:\n%s" % self.emit()
		
		# otherwise...		
		# i.e. "lib.Worker.Tasks.Documents.evaluate_document"
		task_path = ".".join([TASKS_ROOT, self.task_path])
		p, f = task_path.rsplit(".", 1)

		try:
			module = import_module(p)
			func = getattr(module, f)

			#TODO: for cellery: 
			# args = [(self,), ({'queue' :self.queue})]

			args = [self]
			if DEBUG: print args
			
			#p = Process(target=func.apply_async, args=args)
			p = Process(target=func, args=args)
			p.start()
		except Exception as e:
			printAsLog(e)

	def daemonize(self):
		if DEBUG: print "TASK IS NOW BEING DAEMONIZED. LOG FOUND AT %s" % self.log_file
		
		startDaemon(self.log_file, self.pid_file)
		self.daemonized = True
		self.save()
	
	def lock(self, lock=True):
		self.locked = lock
		self.save()
	
	def unlock(self):
		self.lock(lock=False)

	def die(self):
		if hasattr(self, "daemonized") and self.daemonized:
			stopDaemon(self.pid_file)
			self.daemonized = False
			self.save()
	
	def finish(self):
		if DEBUG: print "task finished!"
		self.die()
		
		if not hasattr(self, 'persist') or not self.persist:
			if DEBUG: print "task will be deleted!"

			self.setStatus(200)
			self.delete()
		else:
			self.setStatus(205)
			self.save()
			if DEBUG: print "task will run again after %d minutes" % self.persist
			
			try:
				cron = CronTab(tabfile=os.path.join(MONITOR_ROOT, "uv_cron.tab"))
				
				# if we already have a cron entry, let's make sure it's on
				job = cron.find_comment(self.task_path).next()				
				if not job.is_enabled(): job.enable()
				
				if DEBUG:
					print "this task %s is already registered in our crontab" % self._id
				
				return
				
			except IOError as e:
				if DEBUG: print "no crontab yet..."
				cron = CronTab(tab='# Unveillance CronTab')
			except StopIteration as e:
				if DEBUG: print "this job isn't in cron yet..."
				pass
			
			with settings(warn_only=True):
				PYTHON_PATH = local("which python", capture=True)
	
			task_script = os.path.join(BASE_DIR, "run_task.py")
			job = cron.new(
				command="%s %s %s >> %s" % (PYTHON_PATH, task_script, self._id, os.path.join(MONITOR_ROOT, "api.log.txt")),
				comment=self.task_path)
			
			job.every(self.persist).minutes()
			job.enable()
			cron.write(os.path.join(MONITOR_ROOT, "uv_cron.tab"))
			
			with settings(warn_only=True):
				local("crontab %s" % os.path.join(MONITOR_ROOT, "uv_cron.tab"))
	
	def delete(self):
		if DEBUG: print "DELETING MYSELF"

		with settings(warn_only=True):
			local("rm -rf %s" % os.path.join(ANNEX_DIR, self.base_path))

		return super(UnveillanceTask, self).delete(self._id)
	
	def setStatus(self, status):
		self.status = status
		self.save()