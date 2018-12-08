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

VIRTUALENV_PATH = '/usr/lib/virtualenv'
PIP_REQUIREMENTS = ('git+https://github.com/e9wikner/tellsticklogger.git',)
PY = VIRTUALENV_PATH + '/tellsticklogger/bin/python'
BUILD_PATH = Path('/tmp/telldus-temp')
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
    run('apt install cmake libconfuse-dev libftdi-dev help2man python3 '
         'python-virtualenv -y')


def build():
    """Perform telldus-core build and install it"""
    BUILD_PATH.mkdir(exist_ok=True) 
    with cd(BUILD_PATH):
        run('apt --compile source telldus-core -yq')


def install_telldus():
    deb_packages = ' '.join((p.name for p in BUILD_PATH.glob('*.deb'))
    run('dpkg --install {}'.format(deb_packages))
    

def setup_telldus():
    """ Sets up the telldus core service"""
    apt_configure_telldus_repository()
    install_build_dependencies()

    build()
    install_telldus()
    assert Path('/etc/init.d/telldusd').exists()

    shutil.rmtree(builddir.name, ignore_errors=True)


def setup():
    """ Creates a virtual environment and install required packages"""
    run('apt install python3 -yq')
    telldus_daemon_init = Path('/etc/init.d/telldusd')
    if not telldus_daemon_init.exists():
        setup_telldus()
    else:
        print('Skip telldus install since {} already exists'
              .format(telldus_daemon_init))


    if not Path(VIRTUALENV_PATH).exists():
        run('mkdir -p ' + VIRTUALENV_PATH)
    run('chown {0}:{0} {1}'.format(USER, VIRTUALENV_PATH))

    if not Path(PY).exists():
        run('virtualenv -p python3 ' + VIRTUALENV_PATH + '/tellsticklogger')

    run(PY + ' -m pip install ' + ' '.join(PIP_REQUIREMENTS))


def deploy():
    """Deploy scripts and services"""
    backup_dir = 'backup/' + str(datetime.now().timestamp())
    os.makedirs(backup_dir)
    exclude_list = ['*.pyc', '.DS_Store', '.Apple*', '__pycache__', '.ipynb*']
    run('rsync -thrv src/ / --backup-dir {} --dry-run'.format(backup_dir))
    run("mkdir -p /var/lib/tellsticklogger")
    run("systemctl daemon-reload")
    run("chmod +x /usr/local/bin -R")

    # run('mkdir -p .plotly')
    # put('~/.plotly/.credentials', '~/.plotly/.credentials')
    # run('mkdir -p /var/lib/tellsticklogger')

    # TODO:
    #      >>> import plotly.tools as tls
    #      >>> tls.set_credentials_file(username='username', api_key='api-key')


def update():
    run(PY + ' -m pip install --upgrade ' + ' '.join(PIP_REQUIREMENTS))


def main():
    setup()
    setup_telldus()
    deploy()


if __name__ == '__main__':
    main()