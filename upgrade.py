#!/usr/bin/env python
import argparse

from utils import *
from install import VIRTUALENV_ROOT, SERVICES


def upgrade_system():
    run('apt update -y')
    run('apt upgrade -y')


def upgrade_homeassistant():
    run('systemctl stop homeassistant')
    run('sudo -u {user} {virtualenv}/{user}/bin/pip install --upgrade {user}'
        .format(user='homeassistant', virtualenv=VIRTUALENV_ROOT))
    run('systemctl start homeassistant')


def upgrade(system=True, homeassistant=True):
    if system:
        upgrade_system()
    if homeassistant:
        upgrade_homeassistant()


def main():
    parser = argparse.ArgumentParser(description='By default upgrade everything')
    parser.add_argument('-s', '--system', action='store_true', help='Upgrade system')
    parser.add_argument('-a', '--homeassistant', action='store_true', help='Upgrade homeassistant')
    args = parser.parse_args()
    if not (args.system or args.homeassistant):
        upgrade()
    else:
        upgrade(**args.__dict__)


if __name__ == '__main__':
    main()
