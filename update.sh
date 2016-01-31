#! /bin/bash
THIS_DIR=`pwd`
PROJECT_DIR=../../

# update config if changed
update_config(){
	echo "CONFIG UPDATE TBD"
}

# update setup scripts if changed
update_setup(){
	ls $PROJECT_DIR/setup_extras
	if [ $? -eq 0 ]; then
		cd $PROJECT_DIR/setup && ./setup_extras.sh
	fi
}

# update tasks if changed
update_tasks(){
	ls $PROJECT_DIR/Tasks
	if [ $? -eq 0 ]; then
		cd $THIS_DIR/lib/Worker/Tasks
		ln -s $PROJECT_DIR/Tasks/* .
		ls -la
	fi
}

# update models if changed
update_models(){
	ls $PROJECT_DIR/Models
	if [ $? -eq 0 ]; then
		cd $THIS_DIR/lib/Worker/Models
		ln -s $PROJECT_DIR/Models/* .
		ls -la
	fi
}

show_usage(){
	echo "_________________________"
	echo "Updater Help"
	echo "_________________________"

	echo "./update.sh [config|tasks|models|modules|all]"
}

case "$1" in
	config)
		update_config
		;;
	setup)
		update_setup
		;;
	tasks)
		update_tasks
		;;
	models)
		update_models
		;;
	all)
		update_config
		update_setup
		update_tasks
		update_models
		;;
	*)
		show_usage
		exit 1
esac

cd $THIS_DIR && ./restart.sh
exit 0
