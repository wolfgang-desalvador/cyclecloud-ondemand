import shutil
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from utilities import readOnDemandConfiguration, writeOnDemandConfiguration, getSecretValue, getJetpackConfiguration, executeCommandList
from constants import OOD_CERT_LOCATION, OOD_KEY_LOCATION


config = getJetpackConfiguration()

authenticationType = config['ondemand']['ssl']['SSLType']

onDemandConfiguration = readOnDemandConfiguration()

onDemandConfiguration['ssl'] = [
    'SSLCertificateFile "{}"'.format(OOD_CERT_LOCATION),
    'SSLCertificateKeyFile "{}"'.format(OOD_KEY_LOCATION)
]

writeOnDemandConfiguration(onDemandConfiguration)

if authenticationType == 'self_signed':

    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with open(OOD_KEY_LOCATION, "wb") as f:
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
        # Our certificate will be valid for 1 year
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(config['ondemand']['portal']['serverName'])]),
        critical=False,
    # Sign our certificate with our private key
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=0),
        critical=False
    ).sign(key, hashes.SHA256())

    # Write our certificate out to disk.
    with open(OOD_CERT_LOCATION, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    shutil.copy(OOD_CERT_LOCATION, '/etc/pki/ca-trust/source/anchors')
    executeCommandList([
        "update-ca-trust"
    ])

elif authenticationType == 'keyvault':
    with open(OOD_CERT_LOCATION, 'w') as fid:
        fid.write(getSecretValue(config['keyVaultName'], config['ssl']['certficateName']))

    with open(OOD_KEY_LOCATION, 'w') as fid:
        fid.write(getSecretValue(config['keyVaultName'], config['ssl']['certficateKeyName']))
