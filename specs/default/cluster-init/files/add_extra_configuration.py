import yaml

from utilities import writeOnDemandConfiguration, getJetpackConfiguration, readOnDemandConfiguration

config = getJetpackConfiguration()

extraConfiguration = config['ondemand']['portal']['extraConfiguration']

if extraConfiguration:
    ondemandConfiguration = readOnDemandConfiguration()

    ondemandConfiguration.update(yaml.safe_load(config['ondemand']['portal']['extraConfiguration']))

    writeOnDemandConfiguration(ondemandConfiguration)