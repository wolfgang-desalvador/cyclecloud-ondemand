import json
import subprocess

from utilities import readOnDemandConfiguration, writeOnDemandConfiguration, getJetpackConfiguration


config = getJetpackConfiguration()

onDemandConfiguration = readOnDemandConfiguration()

onDemandConfiguration['servername'] = config['ondemand']['portal']['serverName']

writeOnDemandConfiguration(onDemandConfiguration)