#!/bin/bash
yum install -y epel-release
systemctl disable firewalld --now
setenforce 0
 

yum groupinstall -y "Server with GUI"
wget https://raw.githubusercontent.com/TurboVNC/repo/main/TurboVNC.repo -O /etc/yum.repos.d/TurboVNC.repo
yum install -y turbovnc git
yum groupinstall -y xfce
yum install -y nmap
git clone https://github.com/novnc/websockify.git
cd websockify
git checkout v0.10.0
sed -i "s/'numpy'//g" setup.py
python3 setup.py install
ln -s /usr/local/bin/websockify /usr/bin/websockify 
echo '#!/bin/bash' > /etc/profile.d/desktop.sh
echo 'export PATH=/opt/TurboVNC/bin:$PATH' >> /etc/profile.d/desktop.sh
echo 'export WEBSOCKIFY_CMD=/usr/local/bin/websockify' >> /etc/profile.d/desktop.sh
