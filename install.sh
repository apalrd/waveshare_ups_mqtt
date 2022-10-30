#Install stuff through apt
echo "Install python3-smbus and python3-pip via apt"
sudo apt install python3-smbus python3-pip

#Install stuff through pip
echo "Install paho-mqtt and pyyaml through pip"
sudo pip3 install paho-mqtt pyyaml

#Copy script to /usr/local/bin
echo "Copy python code into /usr/local/bin/"
sudo cp -v *.py /usr/local/bin/
sudo chmod 774 /usr/local/bin/waveshare_ups.py

#Copy yaml but don't overwrite
CONFIG=/etc/waveshare_ups.yaml
echo "Copy config to $CONFIG if it doesn't exist already"
sudo cp -v -n waveshare_ups.yaml /etc/
sudo chmod 664 $CONFIG

#Copy systemd script, run daemon-reload
echo "Copy service file"
SERVICE=waveshare_ups.service
sudo cp -v $SERVICE /etc/systemd/system/$SERVICE
sudo chmod 664 /etc/systemd/system/$SERVICE
echo "Reload systemd daemons"
sudo systemctl daemon-reload