#!/bin/bash
#
# changeMonitor.sh
#
#

PYTHONIOENCODING=UTF-8

if [ -z "$change_monitor_home" ] 
then  
    change_monitor_home="PUT-HERE-THE-HOME-OF-YOUR-APPLICATION"
    PYTHONPATH="$change_monitor_home"
    PYTHON_HOME="$change_monitor_home/.env"
    PATH="$PYTHON_HOME/bin:$PATH"
    PYTHON_EXE="$PYTHON_HOME/bin/python"
fi

"$PYTHON_EXE" -u "$change_monitor_home/main.py" \
--config="config.yaml" \
--logging="logging.json" \
$1 $2 $3 $4 $5


