import subprocess
import yaml
import json

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from constants import OOD_CONFIG_PATH


def executeCommandList(commandList, monitor=False):   
    for command in commandList:
        process = subprocess.Popen(command.split(" "))
        process.wait()

        if monitor and process.returncode != 0:
            raise RuntimeError('The installation process failed unexpectedly, please check output')

def getOutputFromCommand(command):   
    return subprocess.check_output(command.split(" "))

def getRHELVersion():
    return str(getOutputFromCommand("lsb_release -rs").decode()[0])

def readOnDemandConfiguration():
    with open(OOD_CONFIG_PATH, 'r') as fid:
        onDemandConfiguration = yaml.load(fid, Loader=yaml.Loader)  
    
    if onDemandConfiguration is None:
        onDemandConfiguration = {}

    return onDemandConfiguration


def writeOnDemandConfiguration(configuration):
    with open(OOD_CONFIG_PATH, 'w') as fid:
        yaml.dump(configuration, fid)


def getSecretValue(keyVaultName, secretName):
    vaultURL = "https://" + keyVaultName + ".vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vaultURL, credential=credential)
    return client.get_secret(secretName).value

def concatenateToOnDemandConfiguration(configuration):
    with open(OOD_CONFIG_PATH, 'a') as fid:
        for line in configuration:
            fid.write(line)

def createUserAndGroup(name, UID, GID):
    executeCommandList([
        "groupadd -g {} {}".format(GID, name),
        "useradd -u {} -g {} {}".format(UID, GID, name)
    ])

def getJetpackConfiguration():
    return json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))