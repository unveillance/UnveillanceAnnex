#! /bin/bash
THIS_DIR=`pwd`
PROJECT_DIR=$(dirname $(dirname $THIS_DIR))

# update setup scripts if changed
update_plugins(){
	if [ -d $PROJECT_DIR/Plugins ]; then
		python $THIS_DIR/update_plugins.py $PROJECT_DIR
		if [ $? -eq 0 ] && [ -f $PROJECT_DIR/.routine.sh ]; then
			echo "updating plugins..."

			source ~/.bash_profile
			sudo apt-get -yq update
			
			cd $PROJECT_DIR
			chmod +x .routine.sh
			./.routine.sh
			rm .routine.sh
		fi
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

update_framework(){
	cd $THIS_DIR
	git pull origin master
	cd $THIS_DIR/lib/Core
	git pull origin master
}

show_usage(){
	echo "_________________________"
	echo "Updater Help"
	echo "_________________________"

	echo "./update.sh [tasks|models|modules|all]"
}

# pull from head
cd $PROJECT_DIR
git reset --hard HEAD

case "$1" in
	plugins)
		update_plugins
		;;
	tasks)
		update_tasks
		;;
	models)
		update_models
		;;
	framework)
		update_framework
		;;
	all)
		update_plugins
		update_tasks
		update_models
		;;
	*)
		show_usage
		exit 1
esac

cd $THIS_DIR && ./restart.sh
exit 0
