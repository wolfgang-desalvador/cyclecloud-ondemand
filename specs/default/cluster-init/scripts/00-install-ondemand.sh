#!/bin/bash

SCRIPT_FOLDER="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PYTHON_INTERPRETER="/opt/cycle/ondemand"


yum install -y centos-release-scl epel-release

yum install -y https://yum.osc.edu/ondemand/3.0/ondemand-release-web-3.0-1.noarch.rpm

yum install -y ondemand

yum install -y python3

yum install -y ondemand-dex

systemctl start httpd24-httpd
systemctl enable httpd24-httpd

/usr/bin/python3 -m venv ondemand $PYTHON_INTERPRETER
source $PYTHON_INTERPRETER/bin/activate
$PYTHON_INTERPRETER/bin/python -m pip install --upgrade pip
$PYTHON_INTERPRETER/bin/python -m pip install azure-keyvault-secrets azure-identity
