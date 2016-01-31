#! /bin/bash
THIS_DIR=`pwd`
PROJECT_DIR=$(dirname $(dirname $THIS_DIR))

# update setup scripts if changed
update_modules(){
	if [ -d $PROJECT_DIR/Modules ]; then
		echo "updating modules..."
		cd $PROJECT_DIR/Modules && ls
	fi
}

# update tasks if changed
update_tasks(){
	if [ -d $PROJECT_DIR/Tasks ]; then
		echo "updating tasks..."
		cd $THIS_DIR/lib/Worker/Tasks
		ln -s $PROJECT_DIR/Tasks/* .
		ls -la
	fi
}

# update models if changed
update_models(){
	if [ -d $PROJECT_DIR/Models ]; then
		echo "updating models..."
		cd $THIS_DIR/lib/Worker/Models
		ln -s $PROJECT_DIR/Models/* .
		ls -la
	fi
}

show_usage(){
	echo "_________________________"
	echo "Updater Help"
	echo "_________________________"

	echo "./update.sh [tasks|models|modules|all]"
}

case "$1" in
	modules)
		update_modules
		;;
	tasks)
		update_tasks
		;;
	models)
		update_models
		;;
	all)
		update_modules
		update_tasks
		update_models
		;;
	*)
		show_usage
		exit 1
esac

cd $THIS_DIR && ./restart.sh
exit 0
