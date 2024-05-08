import sys
import shutil
import datetime
import yaml
import os
import base64

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import rsa

from utilities import  getRHELVersion, createUserAndGroup, executeCommandList, readOnDemandConfiguration, writeOnDemandConfiguration, \
      getSecretValue, readOnDemandConfiguration, writeOnDemandConfiguration, getJetpackConfiguration, executeCommandList
from constants import OOD_CONFIG_PATH, OOD_CERT_LOCATION, OOD_KEY_LOCATION, SLURM_PACKAGE_NAMES, CONFIGURATION_COMPLETED, OOD_INTERMEDIATE_CERT_LOCATION, RUBY_VERSION_MAPPING, NODE_JS_VERSION_MAPPING
from logger import OnDemandCycleCloudLogger


class OpenOnDemandInstaller():
    def __init__(self) -> None:
        self.cycleCloudOnDemandSettings = getJetpackConfiguration()
        self.logger = OnDemandCycleCloudLogger
        self.osVersion = getRHELVersion()

    @staticmethod
    def _isConfigured():
        return os.path.exists(CONFIGURATION_COMPLETED)

    def _logConfiguration(self, configuration):
        self.logger.debug('New configuration looks like {}'.format(configuration))  

    def _configureAuthenticationBasic(self):
        self.logger.debug('The selected OS Version is {}'.format(self.osVersion))
        if self.osVersion == "7":
            executeCommandList([
                "yum -y install mod_authnz_pam",
                "cp /usr/lib64/httpd/modules/mod_authnz_pam.so /opt/rh/httpd24/root/usr/lib64/httpd/modules/",
                "mkdir -p /opt/rh/httpd24/root/etc/httpd/conf.modules.d/",
                "cp /etc/pam.d/sshd /etc/pam.d/ood",
                "chmod 640 /etc/shadow",
                "chgrp apache /etc/shadow"
            ])

            with open('/opt/rh/httpd24/root/etc/httpd/conf.modules.d/55-authnz_pam.conf', 'w') as fid:
                fid.write('LoadModule authnz_pam_module modules/mod_authnz_pam.so')
            
        elif self.osVersion == "8":
            executeCommandList([
                "yum -y install mod_authnz_pam",
                "mkdir -p /etc/httpd/conf.modules.d/",
                "cp /etc/pam.d/sshd /etc/pam.d/ood",
                "chmod 640 /etc/shadow",
                "chgrp apache /etc/shadow"
            ])

            with open('/etc/httpd/conf.modules.d/55-authnz_pam.conf', 'w') as fid:
                fid.write('LoadModule authnz_pam_module modules/mod_authnz_pam.so')
        else:
            self.logger.error('Unsupported OS in the configuration. Exiting...')
            sys.exit(1)

        onDemandConfiguration = readOnDemandConfiguration()

        self.logger.debug('Writing basic authentication configuration to {}'.format(OOD_CONFIG_PATH))

        onDemandConfiguration['auth'] = [
            "AuthType Basic",
            "AuthName 'Open OnDemand'",
            "AuthBasicProvider PAM",
            "AuthPAMService ood",
            "Require valid-user"
        ]

        self._logConfiguration(onDemandConfiguration)

        writeOnDemandConfiguration(onDemandConfiguration)

    def _configureAuthenticationOIDC_AD(self):
        onDemandConfiguration = readOnDemandConfiguration()

        onDemandConfiguration['auth'] = [
            "AuthType openid-connect",
            "Require valid-user",
        ]

        onDemandConfiguration['logout_redirect'] = "/oidc?logout=https%3A%2F%2F{}".format(
            self.cycleCloudOnDemandSettings['ondemand']['portal']['serverName']
        )
        onDemandConfiguration['oidc_provider_metadata_url'] = self.cycleCloudOnDemandSettings['ondemand']['auth']['oidcAAD']['MetadataURL']
        onDemandConfiguration['oidc_client_id'] = self.cycleCloudOnDemandSettings['ondemand']['auth']['oidcAAD']['ClientID']

        onDemandConfiguration['oidc_client_secret'] = getSecretValue(
            self.cycleCloudOnDemandSettings['ondemand']['keyVaultName'], self.cycleCloudOnDemandSettings['ondemand']['auth']['oidcAAD']['ClientSecretName']
        )

        onDemandConfiguration.update({
            "oidc_uri": "/oidc",
            "oidc_remote_user_claim": self.cycleCloudOnDemandSettings['ondemand']['auth']['oidcAAD']['oidc_remote_user_claim'],
            "oidc_scope": self.cycleCloudOnDemandSettings['ondemand']['auth']['oidcAAD']['oidc_scope'],
            "oidc_session_inactivity_timeout": 28800,
            "oidc_session_max_duration": 28800,
            "oidc_state_max_number_of_cookies": "10 true",
            "oidc_settings": {
                "OIDCPassIDTokenAs": "serialized",
                "OIDCPassRefreshToken": "On",
                "OIDCPassClaimsAs": "environment",
                "OIDCStripCookies": "mod_auth_openidc_session mod_auth_openidc_session_chunks mod_auth_openidc_session_0 mod_auth_openidc_session_1",
                "OIDCResponseType": "code"
            }
        })

        self._logConfiguration(onDemandConfiguration)
        writeOnDemandConfiguration(onDemandConfiguration)

    def _configureAuthenticationOIDC_LDAP(self):
        onDemandConfiguration = readOnDemandConfiguration()

        oidcLDAP = self.cycleCloudOnDemandSettings['ondemand']['auth']['oidc_ldap']

        onDemandConfiguration['auth'] = [
            "AuthType openid-connect",
            "Require valid-user",
        ]

        onDemandConfiguration['dex'] = {
            'connectors': [
                {
                    'type': 'ldap',
                    'id': 'ldap',
                    'name': 'LDAP',
                    'config': {
                        'host': oidcLDAP['ldapHost'],
                        'insecureSkipVerify': False,
                        'bindDN': oidcLDAP['bindDN'],
                        'bindPW': getSecretValue(self.cycleCloudOnDemandSettings['ondemand']['keyVaultName'], oidcLDAP['ldapBindPWName']),
                        'userSearch': {
                            'baseDN': oidcLDAP['userBaseDN'],
                            'filter': oidcLDAP['userFilter'],
                            'username': oidcLDAP['userName'],
                            'idAttr': oidcLDAP['idAttribute'],
                            'emailAttr': oidcLDAP['emailAttribute'],
                            'nameAttr': oidcLDAP['nameAttribute'],
                            'preferredUsernameAttr': oidcLDAP['preferredUsernameAttribute']
                        },
                        'groupSearch': {
                            'baseDN':  oidcLDAP['groupBaseDN'],
                            'filter': oidcLDAP['groupFilter'],
                            'userMatchers': [
                                {
                                    'userAttr': oidcLDAP['groupUserMatcherAttribute'],
                                    'groupAttr': oidcLDAP['groupMatcherAttribute']
                                }
                            ],
                            'nameAttr': oidcLDAP['groupNameAttribute']
                        }
                    }
                }
            ]
        }

        if oidcLDAP['requiresLDAPCert']:
            with open('/etc/ssl/ldap.crt', 'w') as fid:
                fid.write(getSecretValue(self.cycleCloudOnDemandSettings['ondemand']['keyVaultName'], oidcLDAP['ldapCertName']))

            onDemandConfiguration['dex']['connectors'][0]['config']['rootCA'] = '/etc/ssl/ldap.crt'

        self._logConfiguration(onDemandConfiguration)
        writeOnDemandConfiguration(onDemandConfiguration)
        
        executeCommandList([
            "/opt/ood/ood-portal-generator/sbin/update_ood_portal"
            "systemctl enable ondemand-dex",
            "systemctl restart ondemand-dex"
        ])

    def _configureSelfSignedSSL(self):
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
            x509.NameAttribute(NameOID.COMMON_NAME, self.cycleCloudOnDemandSettings['ondemand']['portal']['serverName']),
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
            x509.SubjectAlternativeName([x509.DNSName(self.cycleCloudOnDemandSettings['ondemand']['portal']['serverName'])]),
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
    
    def _configureKeyVaultSSL(self):
        certificate = getSecretValue(self.cycleCloudOnDemandSettings['ondemand']['keyVaultName'], self.cycleCloudOnDemandSettings['ondemand']['ssl']['certificateName'])

        certificateBytes = base64.b64decode(certificate)
        key, cert, _ = pkcs12.load_key_and_certificates(
            data=certificateBytes,
            password=None
        )
        
        # Write our key out to disk.
        with open(OOD_KEY_LOCATION, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        # Write our cert out to disk.
        with open(OOD_CERT_LOCATION, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        if self.cycleCloudOnDemandSettings['ondemand']['ssl']['intermediateCertificate']:
            intermediateCertificateName = self.cycleCloudOnDemandSettings['ondemand']['ssl']['intermediateCertificateName']
            # Write our intermediate cert out to disk.
            with open(OOD_INTERMEDIATE_CERT_LOCATION, "w") as f:
                f.write(getSecretValue(intermediateCertificateName))

    def _configurePBS(self):
        schedulerVersion = self.cycleCloudOnDemandSettings['ondemand']['scheduler']['pbsVersion']
        schedulerHost = self.cycleCloudOnDemandSettings['ondemand']['scheduler']['host']
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
    
    def _configureSLURM(self):
        schedulerHost = self.cycleCloudOnDemandSettings['ondemand']['scheduler']['host']
        schedulerVersion = self.cycleCloudOnDemandSettings['ondemand']['scheduler']['slurmVersion']
        slurmClusterName = self.cycleCloudOnDemandSettings['ondemand']['slurmClusterName']

        slurmBinaryName = "slurm-{}-1.el{}.x86_64.rpm".format(
                schedulerVersion, self.osVersion)

        createUserAndGroup("slurm", self.cycleCloudOnDemandSettings['ondemand']['scheduler']['slurmUID'], self.cycleCloudOnDemandSettings['ondemand']['scheduler']['slurmGID'])
        createUserAndGroup("munge", self.cycleCloudOnDemandSettings['ondemand']['scheduler']['mungeUID'], self.cycleCloudOnDemandSettings['ondemand']['scheduler']['mungeGID'])

        executeCommandList([
            "yum install -y munge"
        ])

        if os.path.exists("/sched/{}".format(slurmClusterName)):
            configurationPath = "/sched/{}".format(slurmClusterName)
        else:
            configurationPath = "/sched"
        
        executeCommandList([
            "cp -f {}/munge.key /etc/munge/".format(configurationPath),
            "chown munge:munge /etc/munge/munge.key",
            "chmod 600 /etc/munge/munge.key",
            "systemctl enable munge --now",
            "systemctl restart munge",
            "mkdir slurm-packages"
        ])

        for package in SLURM_PACKAGE_NAMES:
            executeCommandList([
            "jetpack download {} --project ondemand ./".format(package),
            "tar -xzf {}".format(package),
            "find azure-slurm-install/ -name *.rpm -exec cp -r {} slurm-packages/ ;",
            "rm -rf azure-slurm-install"
            ])
        
        executeCommandList([
            "yum localinstall -y slurm-packages/{}".format(slurmBinaryName),
            "mkdir -p /etc/slurm",
            "ln -sf {}/slurm.conf /etc/slurm/slurm.conf".format(configurationPath),
            "ln -sf {}/gres.conf /etc/slurm/gres.conf".format(configurationPath),
            "ln -sf {}/azure.conf /etc/slurm/azure.conf".format(configurationPath),
            "ln -sf {}/keep_alive.conf /etc/slurm/keep_alive.conf".format(configurationPath),
            "ln -sf {}/cgroup.conf /etc/slurm/cgroup.conf".format(configurationPath),
            "ln -sf {}/accounting.conf /etc/slurm/accounting.conf".format(configurationPath),
        ])

        clusterDefinition = {
            'v2': {
                'metadata': {'title': "Slurm Cluster"},
                'login': {'host': schedulerHost},
                'job': {'host': schedulerHost, 'adapter': 'slurm', 'bin': '/usr/bin', 'conf': '/etc/slurm/slurm.conf'}
            }
        }
        if not os.path.exists('/etc/ood/config/clusters.d/'):
            os.mkdir('/etc/ood/config/clusters.d/')
        yaml.dump(clusterDefinition, open(
            '/etc/ood/config/clusters.d/slurm.yml', 'w'))
    
    def install(self):
        if self._isConfigured():
            self.logger.warn('Skipping installation since already configured')
            self.logger.debug('Install Portal binaries, but link to existing external folders.')
            self.installPortal()
            self.prepareExternalDiskFolders(linkExistingFolders=True)

        else:
            self.logger.debug('Initializing OnDemand Installation')
            self.logger.debug('Prepare directory structure')
            self.prepareExternalDiskFolders()
            self.logger.debug('Install Portal')
            self.installPortal()
            
            self.writeInstallationCompleted()

        self.logger.debug('Initializing authentication configuration')
        self.configureAuthentication()

        self.logger.debug('Initializing SSL configuration')
        self.configureSSL()

        self.logger.debug('Initializing Scheduler Configuration')
        self.configureScheduler()

        self.logger.debug('Adding Server Name')
        self.addServerName()

        self.logger.debug('Adding Extra Configuration')
        self.addExtraConfiguration()

        self.logger.debug('Finalizing OnDemand Installation')
        self.finalizeInstallation()
        
    def configureAuthentication(self):
        authenticationType = self.cycleCloudOnDemandSettings['ondemand']['auth']['AuthType']
        self.logger.debug('The selected authentication type is {}'.format(authenticationType))

        if authenticationType == 'basic':
            self._configureAuthenticationBasic()
        elif authenticationType == 'oidc_aad':
            self._configureAuthenticationOIDC_AD()
        elif authenticationType == 'oidc_ldap':
            self._configureAuthenticationOIDC_LDAP()

    def configureSSL(self):
        sslType = self.cycleCloudOnDemandSettings['ondemand']['ssl']['SSLType']

        onDemandConfiguration = readOnDemandConfiguration()

        onDemandConfiguration['ssl'] = [
            'SSLCertificateFile "{}"'.format(OOD_CERT_LOCATION),
            'SSLCertificateKeyFile "{}"'.format(OOD_KEY_LOCATION)
        ]

        if self.cycleCloudOnDemandSettings['ondemand']['ssl']['intermediateCertificate']:
            onDemandConfiguration['ssl'].append(
                'SSLCertificateChainFile "{}"'.format(OOD_INTERMEDIATE_CERT_LOCATION)
            )

        writeOnDemandConfiguration(onDemandConfiguration)

        if sslType == 'self_signed':
            self._configureSelfSignedSSL()
        elif sslType == 'keyvault':
            self._configureKeyVaultSSL()

    def configureScheduler(self):
        schedulerType = self.cycleCloudOnDemandSettings['ondemand']['scheduler']['type']

        if schedulerType == 'pbs':
            self._configurePBS()
        elif schedulerType == 'slurm':
            self._configureSLURM()

    def addServerName(self):
        onDemandConfiguration = readOnDemandConfiguration()

        onDemandConfiguration['servername'] = self.cycleCloudOnDemandSettings['ondemand']['portal']['serverName']

        self._logConfiguration(onDemandConfiguration)
        writeOnDemandConfiguration(onDemandConfiguration)

    def addExtraConfiguration(self):
        extraConfiguration = self.cycleCloudOnDemandSettings['ondemand']['portal']['extraConfiguration']

        if extraConfiguration:
            ondemandConfiguration = readOnDemandConfiguration()

            ondemandConfiguration.update(yaml.safe_load(extraConfiguration))

            writeOnDemandConfiguration(ondemandConfiguration)

    def writeInstallationCompleted(self):
        with open(CONFIGURATION_COMPLETED, 'w') as fid:
            fid.write('Configuration completed!')

    def prepareExternalDiskFolders(self, linkExistingFolders=False):        
        if linkExistingFolders and not any([os.path.islink(folder) for folder in ['/etc/ood', '/opt/ood', '/var/www/ood']]):
            executeCommandList([
                "mv /etc/ood/ /etc/ood_old",
                "mv /opt/ood/ /opt/ood_old",
                "mv /var/www/ood /var/www/ood_old",
                "ln -s /ood/etc /etc/ood",
                "ln -s /ood/opt /opt/ood",
                "ln -s /ood/www /var/www/ood",
                "rm -rf /opt/rh/httpd24/root/etc/httpd/conf.d/"
            ])

        else:
            executeCommandList([
                "mkdir -p /ood/etc",
                "mkdir -p /ood/opt",
                "mkdir -p /ood/www",
                "mkdir -p /var/www",
                "ln -s /ood/etc /etc/ood",
                "ln -s /ood/opt /opt/ood",
                "ln -s /ood/www /var/www/ood",
            ])
                     
    def installPortal(self):
        self.logger.debug('The selected OS Version is {}'.format(self.osVersion))

        repourl = self.cycleCloudOnDemandSettings['ondemand']['repourl']


        if self.osVersion == "7":
            self.logger.debug("Executing recipe for RHEL 7")
            executeCommandList([
                "yum install -y centos-release-scl epel-release",
                "yum install -y {}".format(repourl),
                "yum install -y ondemand",
                "yum install -y python3",
                "yum install -y ondemand-dex"
            ])
        elif self.osVersion == "8":
            self.logger.debug("Executing recipe for RHEL 8")
            executeCommandList([
                "dnf config-manager --set-enabled powertools",
                "dnf install epel-release -y",
                "dnf module enable ruby:{} nodejs:{} -y".format(RUBY_VERSION_MAPPING[repourl], NODE_JS_VERSION_MAPPING[repourl]),
                "yum install {} -y".format(repourl),
                "yum install -y ondemand-dex",
                "yum install ondemand -y"
            ])

    def finalizeInstallation(self):
        executeCommandList([       
            "rm -rf /var/run/ondemand-nginx/*",
            "chmod 600 /etc/ood/config/ood_portal.yml"
        ])

        if self.osVersion == "7":
            executeCommandList([
                "systemctl restart httpd24-httpd",
                "systemctl enable httpd24-httpd"
            ], monitor=True)
        elif self.osVersion == "8":
            executeCommandList([
                "systemctl restart httpd",
                "systemctl enable httpd",
            ], monitor=True)


if __name__ == '__main__':
    installer = OpenOnDemandInstaller()
    installer.install()