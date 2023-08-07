import json
import subprocess
import yaml
import os

from utilities import executeCommandList

config = json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))

schedulerType = config['ondemand']['scheduler']['type']
schedulerHost = config['ondemand']['scheduler']['host']
schedulerVersion = config['ondemand']['scheduler']['version']


if config['ondemand']['scheduler']['type'] == 'pbs':

    if schedulerVersion.split('.')[0] == '18':
        pbsBinaryName = "pbspro-client-{}-0.x86_64.rpm".format(schedulerVersion)
    else:
        pbsBinaryName = "openpbs-client-{}-0.x86_64.rpm".format(schedulerVersion)

    executeCommandList([
        "jetpack download {} --project ondemand ./".format(pbsBinaryName),
        "yum localinstall -y {}".format(pbsBinaryName)
    ])
    
    clusterDefinition = {
        'v2': {
            'metadata': {'title': "PBS Cluster"},
            'login': {'host': schedulerHost},
            'job': {'host': schedulerHost, 'adapter': 'pbspro', 'exec': '/opt/pbs'}
        }
    }
    if not os.path.exists('/etc/ood/config/clusters.d/'):
        os.mkdir('/etc/ood/config/clusters.d/') 
    yaml.dump(clusterDefinition, open('/etc/ood/config/clusters.d/pbs.yml', 'w'))

