# tellstickipi

## Installation

- Install Raspbian according to https://www.raspberrypi.org/documentation/installation/
- Enable ssh if you are not connecting the PI to a screen and keyboard, https://www.raspberrypi.org/documentation/remote-access/ssh/README.md
- Boot up the PI and login.
- Run `raspi-config` and configure the basics of you Pi.
- Secure the Pi, see https://www.raspberrypi.org/documentation/configuration/security.md
- Update and install dependencies and _tellstickipi_:
    ```
    sudo apt update && sudo apt upgrade -y
    sudo apt install git -y
    git clone https://github.com/e9wikner/tellstickipi.git
    cd tellstickipi && sudo python3 install.py
    ```
- Follow the instructions on screen. If something fails and you don't want to re-run
  the entire install script you can run certain steps like this: 
  `sudo python3 -c "import install; install.deploy(); install.start()"`

- Create link to syncthing root:
  `sudo ln -s /srv/dev-disk-by-label-external/ syncthing_volume`

- Launch:
  `SYNCTHING_USER=$(id -u):$(id -g) docker-compose up`
## Upgrade

When the system is installed it needs to be upgraded. Use `sudo python3 upgrade.py --help`
to get more info on the options. The script will upgrade the system as well as the installed
packages if you don't specify any options.

## Upgrade to a new Pi or a clean install

The upgrade process is not entirely verified but after you have installed the new Pi
here are the steps that you should take.

- Copy the configurations from the previos Pi to the new Pi:
    - `/home/homeassistant/.homeassistant/*.yaml`
    - `/etc/ssmtp/ssmtp.conf`
    - `/etc/tellstick.conf`

- Restart the services:
    ```
    sudo systemctl restart telldusd tellstick_sensorlog homeassistant
    ```


## Links

- Home-Assistant installation instructions: https://www.home-assistant.io/docs/installation/raspberry-pi/
