import re, sys, os
from subprocess import Popen, PIPE
from multiprocessing import Process
from time import sleep

from Models.uv_elasticsearch import UnveillanceElasticsearch
from Models.uv_worker import UnveillanceWorker
from lib.Worker.Models.uv_task import UnveillanceTask

from conf import API_PORT, HOST, ANNEX_DIR, MONITOR_ROOT

class UnveillanceAPI(UnveillanceWorker, UnveillanceElasticsearch):
	def __init__(self):
		print "API started..."
		
		UnveillanceElasticsearch.__init__(self)
		sleep(1)
		UnveillanceWorker.__init__(self)
	
	def fileExistsInAnnex(self, file_path, auto_add=True):
		if file_path == ".gitignore" :
			# WHO IS TRYING TO DO THIS????!
			return False
			
		old_dir = os.getcwd()
		
		os.chdir(ANNEX_DIR)
		cmd0 = ['git', 'annex', 'find', file_path]			
		p0 = Popen(cmd0, stdout=PIPE, close_fds=True)
		data0 = p0.stdout.readline()

		while data0:
			if data0.strip() == file_path:
				if auto_add:
					web_match_found = False
					m_path = re.compile("\s*web: http\://%s:%d/files/%s" % 
						(HOST, API_PORT, file_path))
					cmd1 = ['git', 'annex', 'whereis', file_path]
					p1 = Popen(cmd1, stdout=PIPE, close_fds=True)
					data1 = p1.stdout.readline()
				
					# if this file has not already been added to web remote, add it
					while data1:
						if re.match(m_path, data1) is not None:
							web_match_found = True
							p1.stdout.close()
							break
				
						data1 = p1.stdout.readline()
					
					p1.stdout.close()
				
					if not web_match_found:
						cmd2 = ['git', 'annex', 'addurl', '--file' , file_path,
							'http://%s:%d/files/%s' % (HOST, API_PORT, file_path),
							'--relaxed']
						p2 = Popen(cmd2, stdout=PIPE, close_fds=True)
						data2 = p2.stdout.readline()
						while data2:
							print data2.strip()
							# TODO: handle error
							data2 = p2.stdout.readline()
						p2.stdout().close()
				
				p0.stdout.close()
				os.chdir(old_dir)
				return True
		
			data0 = p0.stdout.readline()
	
		p0.stdout.close()
		os.chdir(old_dir)
		return False
	
	def syncAnnex(self):
		new_file_rx = r'\s*create mode (?:\d+) ([a-zA-Z0-9_\-\./]+)'
		cmd = ['git', 'annex', 'sync']
		p = Popen(cmd0, stdout=PIPE, close_fds=True)
		data = p.stdout.readline()

		while data:
			print data.strip()
			new_file = re.match(new_file_rx, data.strip())
			if len(new_file) == 1:
				# init new file. here it starts.
				print "INIT NEW FILE: %s" % new_file[0]				
				self.setTask(UnveillanceTask("evaluateDocument", file_name=new_file[0]))
				
			data = p.stdout.readline()
		p.stdout.close()