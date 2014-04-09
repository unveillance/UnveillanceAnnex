import signal, os, logging
from sys import exit, argv
from multiprocessing import Process

import tornado.ioloop
import tornado.web
import tornado.httpserver

from api import UnveillanceAPI
from lib.Core.vars import Result
from lib.Core.Utils.funcs import startDaemon, stopDaemon

from conf import ANNEX_DIR, API_PORT, NUM_PROCESSES, HOST, MONITOR_ROOT

def terminationHandler(signal, frame): exit(0)
signal.signal(signal.SIGINT, terminationHandler)

class UnveillanceAnnex(tornado.web.Application, UnveillanceAPI):
	def __init__(self):
		self.api_pid_file = os.path.join(MONITOR_ROOT, "api.pid.txt")
		self.api_log_file = os.path.join(MONITOR_ROOT, "api.log.txt")
		
		self.routes = [
			(r"/files/(\S+)", self.FileHandler), 
			(r"/sync/", self.SyncHandler),
			(r"/(?:(?!files/|sync/))([a-zA-Z0-9_/]*/$)?", self.APIHandler)]
		
		UnveillanceAPI.__init__(self)
	
	class APIHandler(tornado.web.RequestHandler):
		@tornado.web.asynchronous
		def get(self, route):
			res = Result()
			
			self.finish(res.emit())
		
		@tornado.web.asynchronous
		def post(self, route):
			res = Result()
			
			self.finish(res.emit())
			
	
	class SyncHandler(tornado.web.RequestHandler):
		@tornado.web.asynchronous
		def get(self): 
			self.application.syncAnnex()
			res = Result()
			res.result = 200
			self.finish(res.emit())
	
	class FileHandler(tornado.web.RequestHandler):
		@tornado.web.asynchronous
		def get(self, file_path):
			# if file exists in git-annex, return the file
			# else, return 404 (file not found)

			if self.application.fileExistsInAnnex(file_path):
				with open(file_path, 'rb') as file:
					# TODO: set content-type
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
		#startDaemon(self.api_log_file, self.api_pid_file)
		
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