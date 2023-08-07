import json
import subprocess

from utilities import readOnDemandConfiguration, writeOnDemandConfiguration


config = json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))

onDemandConfiguration = readOnDemandConfiguration()

onDemandConfiguration['servername'] = config['ondemand']['portal']['serverName']

writeOnDemandConfiguration(onDemandConfiguration)