#!/usr/bin/env python
from datetime import datetime
import getpass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from utils import *


VIRTUALENV_ROOT = Path("/usr/lib/virtualenv")
TELLSTICKLOGGER_URL = "git+https://github.com/e9wikner/tellsticklogger.git"
TELLSTICK_LOG_DIR = Path("/var/lib/tellsticklogger")
BUILD_PATH = Path("/tmp/telldus-temp")
TELLDUS_DAEMON_INIT = Path("/etc/init.d/telldusd")
SERVICES = "tellstick_sensorlog "
BACKUP_DIR = "backup/" + str(datetime.now().isoformat()).replace(":", "-")


def apt_configure_telldus_repository():
    """Add the debian telldus source to the apt sources list."""
    telldus_source = "deb-src http://download.telldus.com/debian/ unstable main"
    with open("/etc/apt/sources.list.d/telldus.list", mode="w+") as f:
        lines = f.read().splitlines()
        if not telldus_source in lines:
            f.write(telldus_source)

    public_key = curl("http://download.telldus.com/debian/telldus-public.key")
    with tempfile.NamedTemporaryFile(buffering=0) as keyfile:
        keyfile.write(public_key)
        run("apt-key add {}".format(keyfile.name))


def install_build_dependencies():
    """Install telldus-code build dependencies"""
    run("apt update -y")
    run("apt install build-essential -y")
    run("apt build-dep telldus-core -y")
    run("apt install cmake libconfuse-dev libftdi-dev help2man python3 -y")


def build_telldus():
    """Perform telldus-core build and install it"""
    shutil.rmtree(str(BUILD_PATH), ignore_errors=True)
    BUILD_PATH.mkdir(exist_ok=True)
    with cd(BUILD_PATH):
        run("apt --compile source telldus-core -yq")


def install_telldus():
    deb_packages = " ".join((str(p) for p in BUILD_PATH.glob("*.deb")))
    run("dpkg --install {}".format(deb_packages))


def setup_telldus():
    """ Sets up the telldus core service"""
    if TELLDUS_DAEMON_INIT.exists():
        print(
            "Skip telldus install since {} already exists".format(TELLDUS_DAEMON_INIT)
        )
        return
    apt_configure_telldus_repository()
    install_build_dependencies()

    build_telldus()
    install_telldus()
    assert Path("/etc/init.d/telldusd").exists()


def create_virtualenv(user):
    run("apt install python3-venv -yq")
    virtualenv = VIRTUALENV_ROOT / user
    run("python3 -m venv {}".format(virtualenv))
    run("chown -R {0}:{0} {1}".format(user, virtualenv))


def useradd(user, groups=None):
    try:
        run("useradd -rm {}".format(user))
    except subprocess.CalledProcessError as error:
        if 9 == error.returncode:
            print(user + " already exists")
        else:
            raise
    if groups:
        run("usermod --groups {} {}".format(groups, user))


def setup_tellsticklogger():
    """ Create a virtual environment and install required packages"""
    user = "telldus"
    useradd(user)
    setup_telldus()
    create_virtualenv(user)


def deploy():
    """Deploy scripts and services"""
    run("rsync --checksum --recursive -hv src/ / --backup-dir {}".format(BACKUP_DIR))
    TELLSTICK_LOG_DIR.mkdir(exist_ok=True)
    run("systemctl daemon-reload")

    run(f"{VIRTUALENV_ROOT}/telldus/bin/pip install wheel")
    run(f"{VIRTUALENV_ROOT}/telldus/bin/pip install --upgrade {TELLSTICKLOGGER_URL}")

    # run('mkdir -p .plotly')
    # put('~/.plotly/.credentials', '~/.plotly/.credentials')
    # run('mkdir -p /var/lib/tellsticklogger')

    # TODO:
    #      >>> import plotly.tools as tls
    #      >>> tls.set_credentials_file(username='username', api_key='api-key')


def start():
    """Startup tellsticklogger and homeassistant"""
    shutil.chown(str(TELLSTICK_LOG_DIR), user="telldus", group="telldus")
    run("systemctl start " + SERVICES)
    run("systemctl enable " + SERVICES)


def main():
    os.makedirs(BACKUP_DIR)
    setup_tellsticklogger()
    deploy()
    start()
    print("Setup is finished")


if __name__ == "__main__":
    main()
