#! /bin/bash
###
#install ehome.sevice for systemd
###

install_location=$(pwd)

echo ===== Creating and installing SystemD service =====
cat << EOF > /tmp/ehome.service
#Service for eHome running on a SystemD service
#
[Unit]
Description=eHome for Python3
After=syslog.target network.target network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 -u ${install_location}/ehome.py
Restart=on-abort
WorkingDirectory=${install_location}
SyslogIdentifier=ehome

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/ehome.service /etc/systemd/system/
sudo systemctl enable ehome.service