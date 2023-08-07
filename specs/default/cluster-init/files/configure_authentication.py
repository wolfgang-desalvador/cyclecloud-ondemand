import json
import subprocess

config = json.loads(subprocess.check_output(["/opt/cycle/jetpack/bin/jetpack", "config", "--json"]))


authenticationType = config['ondemand']['AuthType']

if authenticationType == 'basic':

    subprocess.check_output('sudo yum -y install mod_authnz_pam'.split(" "))
    subprocess.check_output('sudo cp /usr/lib64/httpd/modules/mod_authnz_pam.so /opt/rh/httpd24/root/usr/lib64/httpd/modules/'.split(" "))
    subprocess.check_output('sudo echo "LoadModule authnz_pam_module modules/mod_authnz_pam.so" > /opt/rh/httpd24/root/etc/httpd/conf.modules.d/55-authnz_pam.conf'.split(" "))
    subprocess.check_output('sudo cp /etc/pam.d/sshd /etc/pam.d/ood'.split(" "))
    subprocess.check_output('sudo chmod 640 /etc/shadow'.split(" "))
    subprocess.check_output('sudo chgrp apache /etc/shadow'.split(" "))
    
    
    with open('/etc/ood/config/ood_portal.yml', 'a')as fid:
        fid.write('auth:\n')
        fid.write('  - "AuthType Basic"\n')
        fid.write('  - "AuthName ""Open OnDemand""\n')
        fid.write('  - "AuthBasicProvider PAM"\n')
        fid.write('  - "AuthPAMService ood"\n')
        fid.write('  - "Require valid-user"      \n')
        
        