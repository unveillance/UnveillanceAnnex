import os
from fabric.api import local, settings

from conf import ANNEX_DIR, getConfig

if __name__ == "__main__":
	this_dir = os.getcwd()
	annex_includes = getConfig('annex_includes')
	
	with settings(warn_only=True):
		os.chdir(ANNEX_DIR)
		local("rm -rf .data")
		local("git annex add .")
		local("git annex sync")
		local("rm *")
		local("git annex add .")
		local("git annex sync")
		local("mkdir .data")
		local("git annex add .")
		local("git annex sync")
	
		if annex_includes is not None:
			for _, _, files in os.walk(annex_includes):
				for f in files:
					local("cp %s ." % os.path.join(annex_includes, f))
					local("git annex add %s" % f)

				# this should not be recursive.
				break

		local("git annex sync")
		os.chdir(this_dir)