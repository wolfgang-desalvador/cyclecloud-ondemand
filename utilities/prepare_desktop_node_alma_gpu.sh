#!/bin/bash
set -xe

yum install -y epel-release
systemctl disable firewalld --now
setenforce 0 
 
cat <<EOF >/etc/modprobe.d/nouveau.conf
Blacklist Nouveau
LBM-Nouveau Blacklist
EOF


### Retrieve latest GRID Driver from https://learn.microsoft.com/en-us/azure/virtual-machines/linux/n-series-driver-setup
wget -O NVIDIA-Linux-x86_64-grid.run https://download.microsoft.com/download/1/4/4/14450d0e-a3f2-4b0a-9bb4-a8e729e986c4/NVIDIA-Linux-x86_64-535.154.05-grid-azure.run
chmod +x NVIDIA-Linux-x86_64-grid.run
sudo ./NVIDIA-Linux-x86_64-grid.run -s


cat <<EOF >>/etc/nvidia/gridd.conf
IgnoreSP=FALSE
EnableUI=FALSE
EOF
sed -i '/FeatureType=0/d' /etc/nvidia/gridd.conf


## ATTENTION - On AlmaLinux 8.7 HPC this will find conflicting moby packages
yum groupinstall -y "Server with GUI"
wget https://raw.githubusercontent.com/TurboVNC/repo/main/TurboVNC.repo -O /etc/yum.repos.d/TurboVNC.repo
wget https://raw.githubusercontent.com/VirtualGL/repo/main/VirtualGL.repo -O /etc/yum.repos.d/VirtualGL.repo
yum install -y turbovnc git
yum install --enablerepo=powertools -y VirtualGL turbojpeg xorg-x11-apps
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


systemctl set-default graphical.target
systemctl isolate graphical.target


cat <<EOF >/etc/rc.d/rc3.d/busidupdate.sh
#!/bin/bash
rmmod nvidia_drm nvidia_modeset NVIDIA || true
/usr/bin/vglserver_config -config +s +f -t

BUSID=\$(nvidia-xconfig --query-gpu-info | awk '/PCI BusID/{print \$4}')
nvidia-xconfig --enable-all-gpus --allow-empty-initial-configuration -c /etc/X11/xorg.conf --virtual=1920x1200 --busid \$BUSID -s
sed -i '/BusID/a\ Option "HardDPMS" "false"' /etc/X11/xorg.conf
echo "Bus updated" >> /var/log/busidupdate.log
EOF
chmod +x /etc/rc.d/rc3.d/busidupdate.sh

cat << EOF > /etc/systemd/system/busidupdate.service
[Unit]
Description=Update bus

[Service]
Type=oneshot
ExecStart=/etc/rc.d/rc3.d/busidupdate.sh

[Install]
WantedBy=gdm.service
EOF

systemctl enable busidupdate.service

cat <<EOF >/etc/profile.d/vglrun.sh
#!/bin/bash
ngpu=\$(/usr/sbin/lspci | grep NVIDIA | wc -l)
alias vglrun='/usr/bin/vglrun -d :0.\$(( \${port:-0} % \${ngpu:-1}))'
EOF


cat << EOF >>/etc/sysctl.conf
net.core.rmem_max=2097152
net.core.wmem_max=2097152
EOF


cat << EOF >> /etc/profile.d/tvnc.sh
export TVNC_WM=xfce-session
EOF

