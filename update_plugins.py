import os, re
from sys import exit, argv
from fabric.api import settings, local
from fabric.context_managers import hide


def scan_for_plugin_updates(annex_path):
	os.chdir(annex_path)
	print os.getcwd()
	updated_plugins = None
	
	with settings(hide('everything'), warn_only=True):
		try:
			for line in local("git log -1 --stat HEAD", capture=True).split('\n'):
				plugin = re.findall(r'\s*Plugins/(\w+)/src/(uv_plugin\.[p|s][y|h])', line)
				
				if not plugin:
					continue

				plugin = plugin[0]

				if updated_plugins is None:
					updated_plugins = {}

				if plugin[0] not in updated_plugins.keys():
					updated_plugins[plugin[0]] = []

				updated_plugins[plugin[0]].append(plugin[1])

		except Exception as e:
			print e, type(e)

	if type(updated_plugins) is not dict:
		return False

	cmd = None
	for r, p in updated_plugins.iteritems():
		if type(cmd) is not list:
			cmd = []

		cmd.append("cd %s" % os.path.join(annex_path, "Plugins", r, "src"))
		
		if "uv_plugin.sh" in p:
			p.insert(0, p.pop(p.index("uv_plugin.sh")))

		cmd.extend(["%s%s" % ("./" if p[-2:] == "sh" else "python ", p) for p in p])
		cmd.append("sleep 2")

	if type(cmd) is list and len(cmd) > 0:
		with open(os.path.join(annex_path, ".routine.sh"), 'wb+') as routine:
			routine.write("#! /bin/bash\n\n")
			routine.write("\n".join(cmd))

		return True

	return False

if __name__ == "__main__":
	exit(0 if scan_for_plugin_updates(argv[1]) else -1)