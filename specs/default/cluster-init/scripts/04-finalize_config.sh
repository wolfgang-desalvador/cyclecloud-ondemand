#!/bin/bash

SCRIPT_FOLDER="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PYTHON_INTERPRETER="/opt/cycle/ondemand"

source $PYTHON_INTERPRETER/bin/activate

$PYTHON_INTERPRETER/bin/python $SCRIPT_FOLDER/../files/add_server_name.py

$PYTHON_INTERPRETER/bin/python $SCRIPT_FOLDER/../files/add_extra_configuration.py

rm -rf /var/run/ondemand-nginx/*

chmod 600 /etc/ood/config/ood_portal.yml


if [ $(lsb_release -rs | cut -f1 -d.) == 7]; then

    systemctl enable --now httpd24-httpd
    systemctl restart httpd24-httpd


elif [ $(lsb_release -rs | cut -f1 -d.) == 8] ; then

    systemctl enable --now httpd
    systemctl restart httpd

fi