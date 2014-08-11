import os, re
from sys import argv, exit

if __name__ == "__main__":
	if len(argv) != 2 or not os.path.exists(argv[1]):
		print "bad usage."
		exit(1)

	from conf import SSH_ROOT
	from fabric.api import settings, local

	with settings(warn_only=True):
		is_key = local("ssh-keygen -l -f %s" % argv[1], capture=True)
		if re.match(re.compile(".*\s%s" % "is not a public key file."), is_key) is not None:
			print "bad key."
			exit(1)

		local("cat %s >> %s" % (argv[1], os.path.join(SSH_ROOT, "authorized_keys")))

	print "KEY IMPORTED:\n%s" % is_key
	exit(0)