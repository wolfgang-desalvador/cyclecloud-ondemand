import json
import subprocess
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from utilities import readOnDemandConfiguration, writeOnDemandConfiguration, getSecretValue, getJetpackConfiguration

config = getJetpackConfiguration()

authenticationType = config['ondemand']['ssl']['SSLType']

onDemandConfiguration = readOnDemandConfiguration()

onDemandConfiguration['ssl'] = [
    'SSLCertificateFile "/etc/ssl/ssl-ondemand.crt"',
    'SSLCertificateKeyFile "/etc/ssl/ssl-ondemand.key"'
]

writeOnDemandConfiguration(onDemandConfiguration)

if authenticationType == 'self_signed':

    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with open("/etc/ssl/ssl-ondemand.key", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, config['ondemand']['portal']['serverName']),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        # Our certificate will be valid for 10 days
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(config['ondemand']['portal']['serverName'])]),
        critical=False,
    # Sign our certificate with our private key
    ).sign(key, hashes.SHA256())

    # Write our certificate out to disk.
    with open("/etc/ssl/ssl-ondemand.crt", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

elif authenticationType == 'keyvault':
    with open('/etc/ssl/ssl-ondemand.crt', 'w') as fid:
        fid.write(getSecretValue(config['keyVaultName'], config['ssl']['certficateName']))

    with open('/etc/ssl/ssl-ondemand.key', 'w') as fid:
        fid.write(getSecretValue(config['keyVaultName'], config['ssl']['certficateKeyName']))
