#!/bin/bash

SCRIPT_FOLDER="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PYTHON_INTERPRETER="/opt/cycle/ondemand"

source $PYTHON_INTERPRETER/bin/activate

$PYTHON_INTERPRETER/bin/python $SCRIPT_FOLDER/configure_authentication.py
