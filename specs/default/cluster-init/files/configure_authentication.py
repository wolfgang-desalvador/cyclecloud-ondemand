import sys

from utilities import  getRHELVersion, executeCommandList, readOnDemandConfiguration, writeOnDemandConfiguration, getSecretValue, getJetpackConfiguration
from constants import OOD_CONFIG_PATH
from logger import OnDemandCycleCloudLogger


config = getJetpackConfiguration()

authenticationType = config['ondemand']['auth']['AuthType']
OnDemandCycleCloudLogger.debug('The selected authentication type is {}'.format(authenticationType))

if authenticationType == 'basic':
    osVersion = getRHELVersion()

    OnDemandCycleCloudLogger.debug('The selected OS Version is {}'.format(osVersion))
    if osVersion == "7":
        executeCommandList([
            "yum -y install mod_authnz_pam",
            "cp /usr/lib64/httpd/modules/mod_authnz_pam.so /opt/rh/httpd24/root/usr/lib64/httpd/modules/",
            "echo ""LoadModule authnz_pam_module modules/mod_authnz_pam.so"" > /opt/rh/httpd24/root/etc/httpd/conf.modules.d/55-authnz_pam.conf",
            "cp /etc/pam.d/sshd /etc/pam.d/ood",
            "chmod 640 /etc/shadow",
            "chgrp apache /etc/shadow"
        ])
        
    elif osVersion == "8":
        executeCommandList([
            "yum -y install mod_authnz_pam",
            "sudo echo ""LoadModule authnz_pam_module modules/mod_authnz_pam.so"" > /etc/httpd/conf.modules.d/55-authnz_pam.conf",
            "cp /etc/pam.d/sshd /etc/pam.d/ood",
            "chmod 640 /etc/shadow",
            "chgrp apache /etc/shadow"
        ])
    else:
        OnDemandCycleCloudLogger.error('Unsupported OS in the configuration. Exiting...')
        sys.exit(1)

    onDemandConfiguration = readOnDemandConfiguration()

    OnDemandCycleCloudLogger.debug('Writing basic authentication configuration to {}'.format(OOD_CONFIG_PATH))

    onDemandConfiguration['auth'] = [
        "AuthType Basic",
        "AuthName ""Open OnDemand""",
        "AuthBasicProvider PAM",
        "AuthPAMService ood",
        "Require valid-user"
    ]

    writeOnDemandConfiguration(onDemandConfiguration)


elif authenticationType == 'oidc_aad':
    onDemandConfiguration = readOnDemandConfiguration()

    onDemandConfiguration['auth'] = [
        "AuthType openid-connect",
        "Require valid-user",
    ]

    onDemandConfiguration['logout_redirect'] = "/oidc?logout=https%3A%2F%2F{}".format(
        config['ondemand']['portal']['serverName']
    )
    onDemandConfiguration['oidc_provider_metadata_url'] = config['ondemand']['auth']['oidcAAD']['MetadataURL']
    onDemandConfiguration['oidc_client_id'] = config['ondemand']['auth']['oidcAAD']['ClientID']

    onDemandConfiguration['oidc_client_secret'] = getSecretValue(
        config['ondemand']['keyVaultName'], config['ondemand']['auth']['oidcAAD']['ClientSecretName']
    )

    onDemandConfiguration.update({
        "oidc_uri": "/oidc",
        "oidc_remote_user_claim": config['ondemand']['auth']['oidcAAD']['oidc_remote_user_claim'],
        "oidc_scope": config['ondemand']['auth']['oidcAAD']['oidc_scope'],
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

    writeOnDemandConfiguration(onDemandConfiguration)

elif authenticationType == 'oidc_ldap':
    onDemandConfiguration = readOnDemandConfiguration()

    oidcLDAP = config['ondemand']['auth']['oidc_ldap']

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
                    'bindPW': getSecretValue(config['ondemand']['keyVaultName'], oidcLDAP['ldapBindPWName']),
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
            fid.write(getSecretValue(config['ondemand']['keyVaultName'], oidcLDAP['ldapCertName']))

        onDemandConfiguration['dex']['connectors'][0]['config']['rootCA'] = '/etc/ssl/ldap.crt'

    writeOnDemandConfiguration(onDemandConfiguration)
    
    executeCommandList([
        "/opt/ood/ood-portal-generator/sbin/update_ood_portal"
        "systemctl enable ondemand-dex",
        "systemctl restart ondemand-dex"
    ])