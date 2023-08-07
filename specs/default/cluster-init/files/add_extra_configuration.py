import json
import subprocess

from utilities import concatenateToOnDemandConfiguration


config = json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))

concatenateToOnDemandConfiguration(config['ondemand']['portal']['extraConfiguration'])