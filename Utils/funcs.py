import pandas
from datetime import datetime

def printAsLog(message, as_error=False):
	ts = pandas.DatetimeIndex([datetime.utcnow()])
	
	message = "%s: %s" % (ts.format()[0], message)
	if as_error:
		message = "[ERROR] %s" % message
	
	print message