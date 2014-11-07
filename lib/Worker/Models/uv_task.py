import os, requests
from crontab import CronTab
from json import dumps
from time import sleep
from importlib import import_module
from multiprocessing import Process
from fabric.api import local, settings

from Models.uv_object import UnveillanceObject
from Utils.funcs import printAsLog
from lib.Core.Utils.funcs import stopDaemon, startDaemon
from lib.Core.Models.uv_task_channel import UnveillanceTaskChannel

from vars import EmitSentinel, UV_DOC_TYPE, TASKS_ROOT, TASK_PERSIST_KEYS, ASSET_TAGS
from conf import DEBUG, BASE_DIR, ANNEX_DIR, HOST, API_PORT, TASK_CHANNEL_PORT, MONITOR_ROOT

class UnveillanceTask(UnveillanceObject):
	def __init__(self, inflate=None, _id=None):
		if inflate is not None:
			if '_id' not in inflate.keys():
				from lib.Core.Utils.funcs import generateMD5Hash
				inflate['_id'] = generateMD5Hash()
	
			inflate['uv_doc_type'] = UV_DOC_TYPE['TASK']
			inflate['status'] = 201
			
		super(UnveillanceTask, self).__init__(_id=_id, inflate=inflate, 
			emit_sentinels=[
				EmitSentinel("ctx", "Worker", None),
				EmitSentinel("log_file", "str", None),
				EmitSentinel("task_channel", "UnveillanceTaskChannel", None)])

		self.pid_file = os.path.join(ANNEX_DIR, self.base_path, "pid.txt")

		if not hasattr(self, "log_file"):
			self.log_file = os.path.join(ANNEX_DIR, self.base_path, "log.txt")
		else:
			if DEBUG: print "INHERITED A LOG FILE: %s" % self.log_file

	def communicate(self, message=None):
		if not hasattr(self, "task_channel"):
			return
		
		if message is None:
			message = {}

		for i in ["_id", "doc_id", "status", "task_path"]:
			try:
				message[i] = getattr(self, i)
			except Exception as e:
				pass

		message['task_type'] = type(self).__name__

		if self.status == 200:
			result_assets = self.getAssetsByTagName(ASSET_TAGS['C_RES'])
			if result_assets is not None:
				message['result_assets'] = [os.path.join(self.base_path, r['file_name']) for r in result_assets]

		url = '/'.join([
			"annex_channel", self.task_channel._session, self.task_channel._id, "xhr_send"])

		r = requests.post("http://%s:%d/%s" % (self.task_channel.host, self.task_channel.port, url),
			data="[%s]" % dumps(message))

		return message

	def signal_terminate(self):
		# meaning, the task should be gone!
		self.setStatus(410)
		self.communicate()
	
	def routeNext(self, inflate=None):
		if DEBUG: print "ROUTING NEXT TASK FROM QUEUE\nCLONING SOME VARS FROM SELF:\n%s" % self.emit()
		
		if hasattr(self, "no_continue"):
			if DEBUG:
				print "NO CONTINUE FLAG DETECTED.  NO ROUTING POSSIBLE."
			
			self.signal_terminate()
			return		
		
		next_task_path = self.get_next()
		if next_task_path is None:
			if DEBUG:
				print "TASK QUEUE EXHAUSTED. NO ROUTING POSSIBLE."

			self.signal_terminate()
			return

		if inflate is None:
			inflate = {}			
		
		for a in TASK_PERSIST_KEYS:
			if hasattr(self, a):
				inflate[a] = getattr(self, a)

		inflate['task_path'] = next_task_path
		next_task = UnveillanceTask(inflate=inflate)
		next_task.run()

	def get_next(self):
		if not hasattr(self, "task_queue"):
			if DEBUG:
				print "TASK HAS NO TASK QUEUE. NO ROUTING POSSIBLE."

			return None

		try:
			task_index = self.task_queue.index(self.task_path) + 1
			return self.task_queue[task_index]
		except Exception as e:
			if DEBUG:
				print e
		
		return None

	def put_next(self, task_paths, after=None):
		if type(task_paths) is not list:
			task_paths = [task_paths]

		if not hasattr(self, "task_queue"):
			self.task_queue = []

		for t in task_paths:
			self.task_queue.append(t)

		self.save()
		
	def run(self):
		self.setStatus(201)	
		# otherwise...		
		# i.e. "lib.Worker.Tasks.Documents.evaluate_document"
		task_path = ".".join([TASKS_ROOT, self.task_path])
		p, f = task_path.rsplit(".", 1)

		# start a websocket for the task
		self.task_channel = UnveillanceTaskChannel("annex_channel", "localhost",
			API_PORT + 1, use_ssl=False)

		try:
			module = import_module(p)
			func = getattr(module, f)

			#TODO: for cellery: 
			# args = [(self,), ({'queue' :self.queue})]

			args = [self]
			if DEBUG: print args
			
			#p = Process(target=func.apply_async, args=args)
			p = Process(target=func, args=args)
			self.communicate()
			sleep(1)
			p.start()

		except Exception as e:
			printAsLog(e)
			self.fail()

	def daemonize(self):
		if DEBUG: print "TASK %s IS NOW BEING DAEMONIZED. LOG FOUND AT %s" % (self.task_path, self.log_file)
		
		startDaemon(self.log_file, self.pid_file)
		self.daemonized = True
		self.save()
	
	def lock(self, lock=True):
		self.locked = lock
		self.save()
	
	def unlock(self):
		self.lock(lock=False)

	def save(self, create=False, built=False):
		if built:
			self.built = True

		super(UnveillanceTask, self).save(create=create)

		if built: self.finish()

	def fail(self, status=None, message=None):
		if DEBUG:
			print "*** FAILING OUT EXPLICITLY ***"

		if status is None:
			status = 404

		self.setStatus(status)
		self.communicate(message=None if message is None else {'error_message' : message})
		self.signal_terminate()
		self.die()

	def die(self):
		if hasattr(self, "daemonized") and self.daemonized:
			stopDaemon(self.pid_file)
			self.daemonized = False
			self.save()

		if hasattr(self, "task_channel"):
			print "also closing task_channel"
			self.task_channel.die()
	
	def finish(self):
		if DEBUG:
			print "task finished!"
		
		if not hasattr(self, 'persist') or not self.persist:
			if DEBUG: print "task will be deleted!"
			self.setStatus(200)
		else:
			write_to_crontab = True
			self.setStatus(205)
			if DEBUG: print "task will run again after %d minutes" % self.persist
			
			try:
				cron = CronTab(tabfile=os.path.join(MONITOR_ROOT, "uv_cron.tab"))
				
				# if we already have a cron entry, let's make sure it's on
				job = cron.find_comment(self.task_path).next()				
				if not job.is_enabled(): job.enable()
				
				if DEBUG:
					print "this task %s is already registered in our crontab" % self._id
				
				write_to_crontab = False
				
			except IOError as e:
				if DEBUG: print "no crontab yet..."
				cron = CronTab(tab='# Unveillance CronTab')
			except StopIteration as e:
				if DEBUG: print "this job isn't in cron yet..."
				pass
			
			if write_to_crontab:
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

		self.communicate()
		self.die()

		if type(self).__name__ != "UnveillanceCluster":
			if not hasattr(self, 'persist') or not self.persist:
				self.delete()
	
	def delete(self):
		'''
		if DEBUG: print "DELETING MYSELF"

		with settings(warn_only=True):
			local("rm -rf %s" % os.path.join(ANNEX_DIR, self.base_path))
		'''

		return super(UnveillanceTask, self).delete(self._id)
	
	def setStatus(self, status):
		self.status = status
		self.save()