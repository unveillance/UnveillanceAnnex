from sys import argv, exit

def import_key(key_file):
	import os
	
	if len(argv) != 2 or not os.path.exists(key_file):
		print "bad usage."
		return False

	import re
	from conf import SSH_ROOT
	from fabric.api import settings, local

	with settings(warn_only=True):
		is_key = local("ssh-keygen -l -f %s" % key_file, capture=True)
		if re.match(re.compile(".*\s%s" % "is not a public key file."), is_key) is not None:
			print "bad key."
			return False

		local("cat %s >> %s" % (key_file, os.path.join(SSH_ROOT, "authorized_keys")))

	print "KEY IMPORTED:\n%s" % is_key
	return True

if __name__ == "__main__":
	if not import_key(argv[1]): exit(-1)
	exit(0)