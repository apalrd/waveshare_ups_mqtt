# waveshare_ups_mqtt
Service to publish Waveshare Pi UPS sensor readings to MQTT

To install:
* Ensure that the raspberry pi has the I2C module enabled using `sudo raspi-config`
* Clone the git repo. Install git if necessary (`sudo apt install git`)
* CD into the git repo and run the install script. It may ask for yout sudo password (`./install.sh`).
* Edit the configuration file `/etc/waveshare_ups.yaml` as required. A default is provided. You must at a minimum configure your MQTT broker.

To update:
* Pull updates from the git repo (`git pull`)
* Run the install script again. It won't replace your existing yaml.

This has been tested with the Waveshare Pi UPS 'B' model (pogo pins, full-sized Pi). It is expected to work with the 'A' and 'C' models as well. The 'A' and 'B' models (for the full sized Pi) use the configuration '32V_2A". The 'C' model (for the Pi Zero) has a different shunt resistor, so the configuration '16V_5A' is used instead.