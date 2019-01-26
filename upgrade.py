#!/usr/bin/env python

from utils import *
from install import VIRTUALENV_ROOT, SERVICES


def upgrade_system():
    run('apt update -y')
    run('apt upgrade -y')


def upgrade_homeassistant():
    run('systemctl stop homeassistant')
    run('{}/homeassistant/bin/pip install --upgrade homeassistant'
        .format(VIRTUALENV_ROOT))
    run('systemctl start homeassistant')


def upgrade():
    upgrade_system()
    upgrade_homeassistant()


if __name__ == '__main__':
    upgrade()
