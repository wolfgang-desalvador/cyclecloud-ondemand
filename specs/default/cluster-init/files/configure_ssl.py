import json
import subprocess
from OpenSSL import crypto, SSL

from .utilities import readOnDemandConfiguration, writeOnDemandConfiguration, getSecretValue


config = json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))

authenticationType = config['ondemand']['SSLType']


onDemandConfiguration = readOnDemandConfiguration()

onDemandConfiguration['ssl'] = [
    'SSLCertificateFile "/etc/ssl/ssl-ondemand.crt"',
    'SSLCertificateKeyFile "/etc/ssl/ssl-ondemand.key"'
]

writeOnDemandConfiguration(onDemandConfiguration)

if authenticationType == 'self_signed':

    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().CN = config['portal']['serverName']
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.add_extensions([
            crypto.X509Extension(b'subjectAltName', False, 'DNS:{}'.format(config['portal']['serverName']).encode())
    ])
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    open('/etc/ssl/ssl-ondemand.crt', "wt").write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    )
    open('/etc/ssl/ssl-ondemand.key', "wt").write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    )
    

elif authenticationType == 'keyvault':
    with open('/etc/ssl/ssl-ondemand.crt', 'w') as fid:
        fid.write(getSecretValue(config['keyVaultName'], config['ssl']['certficateName']))
    
    with open('/etc/ssl/ssl-ondemand.key', 'w') as fid:
        fid.write(getSecretValue(config['keyVaultName'], config['ssl']['certficateKeyName']))

