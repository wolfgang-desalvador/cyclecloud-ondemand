#!/bin/bash

SCRIPT_FOLDER="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PYTHON_INTERPRETER="/opt/cycle/ondemand"

setenforce 0
systemctl disable --now firewalld

yum install -y redhat-lsb

if [ $(lsb_release -rs | cut -f1 -d.) == 7]; then

    rm -rf /opt/rh/httpd24/root/etc/httpd/conf.d/

    mkdir -p /ood/etc
    mkdir -p /ood/opt
    mkdir -p /ood/www
    mkdir -p /var/www/

    ln -s /ood/etc /etc/ood
    ln -s /ood/opt /opt/ood
    ln -s /ood/www /var/www/ood

    yum install -y centos-release-scl epel-release

    yum install -y https://yum.osc.edu/ondemand/3.0/ondemand-release-web-3.0-1.noarch.rpm

    yum install -y ondemand

    yum install -y python3

    yum install -y ondemand-dex

    systemctl start httpd24-httpd
    systemctl enable httpd24-httpd


elif [ $(lsb_release -rs | cut -f1 -d.) == 8] ; then


    dnf config-manager --set-enabled powertools
    dnf install epel-release -y
    dnf module enable ruby:3.0 nodejs:14
    yum install https://yum.osc.edu/ondemand/3.0/ondemand-release-web-3.0-1.noarch.rpm -y

    yum install ondemand -y
    sudo systemctl start httpd
    sudo systemctl enable httpd

fi

/usr/bin/python3 -m venv ondemand $PYTHON_INTERPRETER
source $PYTHON_INTERPRETER/bin/activate
$PYTHON_INTERPRETER/bin/python -m pip install --upgrade pip
$PYTHON_INTERPRETER/bin/python -m pip install azure-keyvault-secrets azure-identity PyYAML