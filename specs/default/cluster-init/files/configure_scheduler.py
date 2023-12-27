import yaml
import os

from utilities import executeCommandList, getJetpackConfiguration, getRHELVersion, createUserAndGroup
from constants import SLURM_PACKAGE_NAME

config = getJetpackConfiguration()

schedulerType = config['ondemand']['scheduler']['type']
schedulerHost = config['ondemand']['scheduler']['host']



if config['ondemand']['scheduler']['type'] == 'pbs':
    schedulerVersion = config['ondemand']['scheduler']['pbsVersion']

    if schedulerVersion.split('.')[0] == '18':
        pbsBinaryName = "pbspro-client-{}-0.x86_64.rpm".format(
            schedulerVersion)
    else:
        pbsBinaryName = "openpbs-client-{}-0.x86_64.rpm".format(
            schedulerVersion)

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
    yaml.dump(clusterDefinition, open(
        '/etc/ood/config/clusters.d/pbs.yml', 'w'))
    
elif config['ondemand']['scheduler']['type'] == 'slurm':
    schedulerVersion = config['ondemand']['scheduler']['slurmVersion']
    osVersion = getRHELVersion() 
    slurmClusterName = config['ondemand']['slurmClusterName']

    slurmBinaryName = "slurm-{}-1.el{}.x86_64.rpm".format(
            schedulerVersion, osVersion)

    if osVersion == "7":
        slurmFolder = "slurm-pkgs-centos7"
    elif osVersion == "8":
        slurmFolder = "slurm-pkgs-rhel8"

    createUserAndGroup("slurm", config['ondemand']['scheduler']['slurmUID'], config['ondemand']['scheduler']['slurmGID'])
    createUserAndGroup("munge", config['ondemand']['scheduler']['mungeUID'], config['ondemand']['scheduler']['mungeGID'])

    executeCommandList([
        "yum install -y munge"
        "cp -f /sched/*/munge.key /etc/munge/",
        "chown munge:munge /etc/munge/munge.key",
        "chmod 600 /etc/munge/munge.key",
        "systemctl enable munge --now",
        "systemctl restart munge",
        "jetpack download {} --project ondemand ./".format(SLURM_PACKAGE_NAME),
        "tar -xzf {}".format(SLURM_PACKAGE_NAME),
        "cd az-slurm-install",
        "cd {}".format(slurmFolder),
        "yum localinstall -y {}".format(slurmBinaryName),
        "ln -sf /sched/{}/slurm.conf /etc/slurm/slurm.conf".format(slurmClusterName),
        "ln -sf /sched/{}/gres.conf /etc/slurm/gres.conf".format(slurmClusterName),
        "ln -sf /sched/{}/azure.conf /etc/slurm/azure.conf".format(slurmClusterName),
        "ln -sf /sched/{}/keep_alive.conf /etc/slurm/keep_alive.conf".format(slurmClusterName),
        "ln -sf /sched/{}/cgroup.conf /etc/slurm/cgroup.conf".format(slurmClusterName),
    ])

    clusterDefinition = {
        'v2': {
            'metadata': {'title': "Slurm Cluster"},
            'login': {'host': schedulerHost},
            'job': {'host': schedulerHost, 'cluster': slurmClusterName, 'adapter': 'slurm', 'bin': '/usr/bin', 'conf': '/etc/slurm/slurm.conf'}
        }
    }
    if not os.path.exists('/etc/ood/config/clusters.d/'):
        os.mkdir('/etc/ood/config/clusters.d/')
    yaml.dump(clusterDefinition, open(
        '/etc/ood/config/clusters.d/slurm.yml', 'w'))