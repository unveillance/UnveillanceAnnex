import signal, os, logging, re, json
from sys import exit, argv
from multiprocessing import Process
from time import sleep
from fabric.api import local, settings

import tornado.ioloop
import tornado.web
import tornado.httpserver

from api import UnveillanceAPI
from lib.Core.vars import Result
from lib.Core.Utils.funcs import startDaemon, stopDaemon
from lib.Worker.Models.uv_task import UnveillanceTask

from conf import ANNEX_DIR, API_PORT, NUM_PROCESSES, HOST, MONITOR_ROOT, DEBUG

def terminationHandler(signal, frame): exit(0)
signal.signal(signal.SIGINT, terminationHandler)

class UnveillanceAnnex(tornado.web.Application, UnveillanceAPI):
	def __init__(self):
		self.api_pid_file = os.path.join(MONITOR_ROOT, "api.pid.txt")
		self.api_log_file = os.path.join(MONITOR_ROOT, "api.log.txt")
		
		self.reserved_routes = ["files", "sync", "task"]
		self.routes = [
			(r"/files/(\S+)", self.FileHandler), 
			(r"/sync/(.+)", self.SyncHandler),
			(r"/task/", self.TaskHandler)]
		
		UnveillanceAPI.__init__(self)
	
	class RouteHandler(tornado.web.RequestHandler):
		@tornado.web.asynchronous
		def get(self, route):  self.routeRequest(route)
		
		def routeRequest(self, route):
			res = Result()
		
			if route is not None:
				route = [r_ for r_ in route.split("/") if r_ != '']				
				func_name = "do_%s" % route[0]
				
				if hasattr(self.application, func_name):
					if DEBUG : print "doing %s" % func_name
					func = getattr(self.application, func_name)
			
					res.result = 200
					res.data = func(self.request)
				else:
					if DEBUG : print "could not find function %s" % func_name

				try:
					if res.data is None: 
						del res.data
						res.result = 412
				except AttributeError as e: pass
						
			self.set_status(res.result)					
			self.finish(res.emit())
	
	class SyncHandler(tornado.web.RequestHandler):			
		@tornado.web.asynchronous
		def get(self, file_name): 
			self.application.syncAnnex(file_name)
			res = Result()
			res.result = 200
			self.finish(res.emit())
		
		@tornado.web.asynchronous
		def post(self, file_name):
			self.application.syncAnnex(file_name, reindex=True)
			res = Result()
			res.result = 200
			self.finish(res.emit())
	
	class TaskHandler(tornado.web.RequestHandler):
		@tornado.web.asynchronous
		def get(self):
			res = Result()
			res.result = 412
			
			res.data = self.application.do_tasks(self)
			if res.data is None:
				del res.data
			elif res.data: res.result = 200
			
			self.set_status(res.result)
			self.finish(res.emit())
		
		@tornado.web.asynchronous
		def post(self):
			res = Result()
			res.status = 412
			
			res.data = self.application.runTask(self)
			if res.data is None:
				del res.data
			elif res.data: res.result = 200
			
			self.set_status(res.result)
			self.finish(res.emit())
	
	class FileHandler(tornado.web.RequestHandler):
		@tornado.web.asynchronous
		def get(self, file_path):
			# if file exists in git-annex, return the file
			# else, return 404 (file not found)

			if self.application.fileExistsInAnnex(file_path):
				with open(os.path.join(ANNEX_DIR, file_path), 'rb') as file:
					# TODO: set content-type
					#self.set_header("Content-Type", "application/octet-stream")
					self.finish(file.read())
				return
			
			# TODO: log this: we want to know who/why is requesting non-entities
			else: self.set_status(404)
			res = Result()
			self.finish(res.emit())

		@tornado.web.asynchronous
		def head(self, file_path):
			res = Result()
			
			# if file exists in git-annex, return 200
			# else, return 405
			
			if self.application.fileExistsInAnnex(file_path): self.set_status(200)
			else: self.set_status(405)
			
			self.finish(res.emit())
	
	def startRESTAPI(self):
		startDaemon(self.api_log_file, self.api_pid_file)
		
		rr_group = r"/(?:(?!%s))([a-zA-Z0-9_/]*/$)?" % "|".join(self.reserved_routes)
		self.routes.append((re.compile(rr_group).pattern, self.RouteHandler))
		tornado.web.Application.__init__(self, self.routes)
		
		server = tornado.httpserver.HTTPServer(self)
		server.bind(API_PORT)
		server.start(NUM_PROCESSES)
	
		tornado.ioloop.IOLoop.instance().start()
	
	def stopRESTAPI(self):
		print "shutting down REST API"
		stopDaemon(self.api_pid_file, extra_pids_port=API_PORT)
		
	def shutdown(self):
		self.stopWorker()
		self.stopElasticsearch()
		self.stopRESTAPI()
	
	def startup(self):
		argv.pop()
		
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		with settings(warn_only=True):
			local("git annex watch")
		os.chdir(this_dir)
		
		p = Process(target=self.startWorker)
		p.start()
		
		p = Process(target=self.startElasticsearch)
		p.start()
		
		p = Process(target=self.startRESTAPI)
		p.start()
			
if __name__ == "__main__":
	os.chdir(ANNEX_DIR)	
	unveillance_annex = UnveillanceAnnex()
	
	if len(argv) != 2: exit("Usage: unveillance_annex.py [-start, -stop, -restart]")
	
	if argv[1] == "-start" or argv[1] == "-firstuse":
		unveillance_annex.startup()
	elif argv[1] == "-stop":
		unveillance_annex.shutdown()
	elif argv[1] == "-restart":
		unveillance_annex.shutdown()
		sleep(5)
		unveillance_annex.startup()