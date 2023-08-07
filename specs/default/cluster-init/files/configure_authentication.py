import json
import subprocess

from utilities import executeCommandList, readOnDemandConfiguration, writeOnDemandConfiguration, getSecretValue


config = json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))

authenticationType = config['ondemand']['auth']['AuthType']


if authenticationType == 'basic':
    executeCommandList([   
        "yum -y install mod_authnz_pam",
        "cp /usr/lib64/httpd/modules/mod_authnz_pam.so /opt/rh/httpd24/root/usr/lib64/httpd/modules/",
        "echo ""LoadModule authnz_pam_module modules/mod_authnz_pam.so"" > /opt/rh/httpd24/root/etc/httpd/conf.modules.d/55-authnz_pam.conf",
        "cp /etc/pam.d/sshd /etc/pam.d/ood",
        "chmod 640 /etc/shadow",
        "chgrp apache /etc/shadow"
    ])
    
    
    onDemandConfiguration = readOnDemandConfiguration()

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

    onDemandConfiguration['logout_redirect'] = "/oidc?logout=https%3A%2F%2F{}".format(config['ondemand']['portal']['serverName'])
    onDemandConfiguration['oidc_provider_metadata_url'] = config['ondemand']['auth']['oidcAAD']['MetadataURL']
    onDemandConfiguration['oidc_client_id'] = config['ondemand']['auth']['oidcAAD']['ClientID']

    onDemandConfiguration['oidc_client_secret'] = getSecretValue(config['ondemand']['keyVaultName'], config['ondemand']['auth']['oidcAAD']['ClientSecretName'])

    onDemandConfiguration.update({
        "oidc_uri": "/oidc",
        "oidc_remote_user_claim": "preferred_username",
        "oidc_scope": "openid profile email",
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
