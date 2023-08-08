#!/bin/bash

SCRIPT_FOLDER="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PYTHON_INTERPRETER="/opt/cycle/ondemand"

source $PYTHON_INTERPRETER/bin/activate

$PYTHON_INTERPRETER/bin/python $SCRIPT_FOLDER/../files/add_server_name.py

$PYTHON_INTERPRETER/bin/python $SCRIPT_FOLDER/../files/add_extra_configuration.py

rm -rf /var/run/ondemand-nginx/*

chmod 600 /etc/ood/config/ood_portal.yml

systemctl enable --now httpd24-httpd
systemctl restart httpd24-httpd
