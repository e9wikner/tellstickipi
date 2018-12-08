# tellstickipi

## Installation

- Install Raspbian according to https://www.raspberrypi.org/documentation/installation/
- Enable ssh if you are not connecting the PI to a screen and keyboard, https://www.raspberrypi.org/documentation/remote-access/ssh/README.md
- Boot up the PI and login.
- Update and install dependencies and _tellstickipi_:
    ```
    sudo apt update && sudo apt upgrade
    sudo apt install git
    git clone https://github.com/e9wikner/tellstickipi.git
    cd tellstickipi && sudo python3 install.py
    ```
- 


## Links

- Home-Assistant installation instructions: https://www.home-assistant.io/docs/installation/raspberry-pi/
