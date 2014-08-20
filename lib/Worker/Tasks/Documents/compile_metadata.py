from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def compileMetadata(task):
	task_tag = "COMPILING METADATA"
	print "\n\n************** %s [START] ******************\n" %  task_tag
	print "compiling metadata for %s" % task.doc_id
	task.setStatus(412)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG
	
	document = UnveillanceDocument(_id=task.doc_id)
	if document is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	metadata = document.loadAsset(task.md_file)
	if metadata is None:
		print "NO METADATA FILE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import csv, re
	from Levenshtein import ratio
	from string import letters
	from vars import METADATA_ASPECTS, ASSET_TAGS
	
	numbers = str("".join([str(i) for i in range(0,10)]))
	missing_value = "NaN"
	
	labels = ["_id"]
	values = [document._id]
	
	try:
		for mda in METADATA_ASPECTS[task.md_namespace]:
			labels.append(mda['label'])
			if hasattr(task, "md_rx"):
				pattern = re.compile(task.md_rx % (mda['tag_position'], mda['label']))
			else:
				pattern = re.compile(mda['tag_position'])
				
			if DEBUG: print pattern.pattern
			
			value = missing_value
			ideal = mda['ideal']
			
			if mda['ideal'] is None:
				if mda['type'] == "str":
					ideal = letters + numbers
				elif mda['type'] == "int":
					ideal = int(numbers)
			
			print "IDEAL FOR TAG: %s" % ideal
			
			for line in metadata.splitlines():
				match = re.findall(pattern, line.strip())
				if len(match) == 1:
					if DEBUG: print "VALUE FOUND: %s (%s)" % (match[0], type(match[0]))
					
					if mda['type'] == "str":
						try:
							value = "%.9f" % ratio(ideal, str(value.replace("\"", '')))
						except TypeError as e:
							if DEBUG: print e
							value = 0

					elif mda['type'] == "int":
						try:
							value = ideal/float(match[0].replace("\"", ''))
						except ZeroDivisionError as e:
							if DEBUG: print e
							value = 0
					break
					
			if value == missing_value:
				if mda['ideal'] is None: value = 1
				else: value = 0
			
			values.append(value)
		
		if hasattr(task, 'md_extras'):
			for key, value in task.md_extras.iteritems():
				labels.append(key)
				values.append(value)
		"""
		if DEBUG:
			print "labels %s" % labels
			print "values %s" % values
		"""

		from cStringIO import StringIO
		
		md_csv_file = StringIO()
		md_csv = csv.writer(md_csv_file, 
			delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

		md_csv.writerow(labels)
		md_csv.writerow(values)
		
		md_asset = document.addAsset(md_csv_file.getvalue(), "file_metadata.csv", 
			tags=[ASSET_TAGS["F_MD"]], 
			description="CSV representation of %s" % task.md_file)
		
		md_csv_file.close()	
		
		if md_asset is None or not document.addFile(md_asset, None, sync=True):
			print "Could not save the Metadata"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			return
		
		document.addCompletedTask(task.task_path)
		
		from lib.Worker.Utils.funcs import routeNextTask
		routeNextTask(task, document)
		
		task.finish()
		print "\n\n************** %s [END] ******************\n" % task_tag
			
	except KeyError as e:
		if DEBUG: print e
		print "No metadata aspects for %s" % task.md_namespace
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return