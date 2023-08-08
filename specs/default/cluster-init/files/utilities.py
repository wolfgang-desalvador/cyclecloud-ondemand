import subprocess
import yaml
import json

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


def executeCommandList(commandList):   
    for command in commandList:
        subprocess.check_output(command.split(" "))


def readOnDemandConfiguration():
    with open('/etc/ood/config/ood_portal.yml', 'r') as fid:
        onDemandConfiguration = yaml.load(fid, Loader=yaml.Loader)  
    
    if onDemandConfiguration is None:
        onDemandConfiguration = {}

    return onDemandConfiguration


def writeOnDemandConfiguration(configuration):
    with open('/etc/ood/config/ood_portal.yml', 'w') as fid:
        yaml.dump(configuration, fid)



def getSecretValue(keyVaultName, secretName):
    vaultURL = "https://" + keyVaultName + ".vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vaultURL, credential=credential)
    return client.get_secret(secretName).value


def concatenateToOnDemandConfiguration(configuration):
    with open('/etc/ood/config/ood_portal.yml', 'a') as fid:
        for line in configuration:
            fid.write(line)


def getJetpackConfiguration():
    return json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))