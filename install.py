#!/usr/bin/env python
from contextlib import contextmanager
from datetime import datetime
import getpass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib import request

VIRTUALENV_ROOT = Path('/usr/lib/virtualenv')
TELLSTICKLOGGER_URL = ('git+https://github.com/e9wikner/tellsticklogger.git',)
BUILD_PATH = Path('/tmp/telldus-temp')
TELLDUS_DAEMON_INIT = Path('/etc/init.d/telldusd')
USER = getpass.getuser()


@contextmanager
def cd(other):
    try:
        this = os.getcwd()
        os.chdir(str(other))
        yield
    finally:
        os.chdir(this)


def run(commandstring):
    print(commandstring)
    subprocess.check_call(commandstring.split())
 

def curl(url):
    with request.urlopen(url) as f:
        return(f.read())


def apt_configure_telldus_repository():
    """Add the debian telldus source to the apt sources list."""
    telldus_source = 'deb-src http://download.telldus.com/debian/ unstable main' 
    with open('/etc/apt/sources.list.d/telldus.list', mode='w+') as f:
        lines = f.read().splitlines()
        if not telldus_source in lines:
            f.write(telldus_source)

    public_key = curl('http://download.telldus.com/debian/telldus-public.key')
    with tempfile.NamedTemporaryFile(buffering=0) as keyfile:
        keyfile.write(public_key)
        run('apt-key add {}'.format(keyfile.name))


def install_build_dependencies():
    """Install telldus-code build dependencies"""
    run('apt update -y')
    run('apt install build-essential -y')
    run('apt build-dep telldus-core -y')
    run('apt install cmake libconfuse-dev libftdi-dev help2man python3 -y')


def build_telldus():
    """Perform telldus-core build and install it"""
    shutil.rmtree(str(BUILD_PATH))
    BUILD_PATH.mkdir(exist_ok=True) 
    with cd(BUILD_PATH):
        run('apt --compile source telldus-core -yq')


def install_telldus():
    deb_packages = ' '.join((str(p) for p in BUILD_PATH.glob('*.deb')))
    run('dpkg --install {}'.format(deb_packages))
   

def setup_telldus():
    """ Sets up the telldus core service"""
    if TELLDUS_DAEMON_INIT.exists():
        print('Skip telldus install since {} already exists'
              .format(TELLDUS_DAEMON_INIT))
        return

    apt_configure_telldus_repository()
    install_build_dependencies()

    build_telldus()
    install_telldus()
    assert Path('/etc/init.d/telldusd').exists()

def create_virtualenv(user, packages):
    run('apt install python3-venv -yq')
    virtualenv = VIRTUALENV_ROOT / user
    run('python3 -m venv {}'.format(virtualenv))
    run('chown -R {0}:{0} {1}'.format(user, virtualenv))


def setup_tellsticklogger():
    """ Create a virtual environment and install required packages"""
    user = 'telldus'
    # run('useradd -rm {}'.format(user))
    setup_telldus()
    create_virtualenv(user, TELLSTICKLOGGER_URL)


def setup_homeassistant():
    """Create a virtual environment and install packages"""
    user = 'homeassistant'
    run('useradd -rm {} -G dialout,gpio'.format(user))
    create_virtualenv(user, user)


def deploy():
    """Deploy scripts and services"""
    backup_dir = 'backup/' + str(datetime.now().timestamp())
    os.makedirs(backup_dir)
    exclude_list = ['*.pyc', '.DS_Store', '.Apple*', '__pycache__', '.ipynb*']
    run('rsync --checksum --recursive -hv src/ / --backup-dir {}'.format(backup_dir))
    run("mkdir -p /var/lib/tellsticklogger")
    run("systemctl daemon-reload")
    run("chmod +x /usr/local/bin -R")

    run('{}/telldus/bin/pip --upgrade install {}'.format(VIRTUALENV_ROOT, TELLSTICKLOGGER_URL))
    run('{}/homeassistant/bin/pip --upgrade install homeassistant'.format(VIRTUALENV_ROOT))

    # run('mkdir -p .plotly')
    # put('~/.plotly/.credentials', '~/.plotly/.credentials')
    # run('mkdir -p /var/lib/tellsticklogger')

    # TODO:
    #      >>> import plotly.tools as tls
    #      >>> tls.set_credentials_file(username='username', api_key='api-key')


def cleanup():
    shutil.rmtree(str(BUILD_PATH), ignore_errors=True)


def main():
    VIRTUALENV_ROOT.mkdir(exist_ok=True)
    setup_tellsticklogger()
    setup_homeassistant()
    deploy()
    cleanup()


if __name__ == '__main__':
    main()