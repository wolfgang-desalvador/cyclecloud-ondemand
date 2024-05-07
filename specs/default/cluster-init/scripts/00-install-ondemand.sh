#!/bin/bash
set -e

SCRIPT_FOLDER="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PYTHON_INTERPRETER="/opt/cycle/ondemand"

setenforce 0
systemctl disable --now firewalld

yum install -y redhat-lsb python3

/usr/bin/python3 -m venv ondemand $PYTHON_INTERPRETER
source $PYTHON_INTERPRETER/bin/activate
$PYTHON_INTERPRETER/bin/python -m pip install --upgrade pip
$PYTHON_INTERPRETER/bin/python -m pip install azure-keyvault-secrets azure-identity PyYAML

source $PYTHON_INTERPRETER/bin/activate

$PYTHON_INTERPRETER/bin/python $SCRIPT_FOLDER/../files/install.py
