#!/usr/bin/env python
import argparse
from contextlib import contextmanager
from datetime import datetime
import getpass
import os
from pathlib import Path
import subprocess

VIRTUALENV_PATH = '/usr/lib/virtualenv'
PIP_REQUIREMENTS = ('git+https://github.com/e9wikner/tellsticklogger.git',)
PY = VIRTUALENV_PATH + '/tellsticklogger/bin/python'
USER = getpass.getuser()


@contextmanager
def cd(other):
    try:
        this = Path.cwd()
        os.chdir(other)
        yield
    finally:
        os.chdir(this)


def run(commandstring):
    print(commandstring)
    subprocess.check_call(commandstring.split())


def setup_telldus():
    """ Sets up the telldus core service.
    """
    run('echo "deb-src http://download.telldus.com/debian/ stable main" >> '
        '/etc/apt/sources.list.d/telldus.list')
    run('wget http://download.telldus.se/debian/telldus-public.key')
    run('apt-key add telldus-public.key')
    run('apt-get update -yq')
    run('apt-get install build-essential -yq')
    run('apt-get build-dep telldus-core -yq')
    run('apt-get install cmake libconfuse-dev libftdi-dev help2man python3 '
         'python-virtualenv -yq')

    tempdir = Path('/tmp').mkdir('telldus-temp', exist_ok=True)

    with cd('telldus-temp'):
        run('apt-get --compile source telldus-core -yq')
        run('dpkg --install *.deb')

    assert Path('/etc/init.d/telldusd').exists()


def setup():
    """ Creates a virtual environment and install required packages
    """
    run('apt-get install python3 -yq')

    if not Path('/etc/init.d/telldusd').exists():
        setup_telldus()

    if not Path(VIRTUALENV_PATH).exists():
        run('mkdir -p ' + VIRTUALENV_PATH)
    run('chown {0}:{0} {1}'.format(USER, VIRTUALENV_PATH))

    if not Path(PY).exists():
        run('virtualenv -p python3 ' + VIRTUALENV_PATH + '/tellsticklogger')

    run(PY + ' -m pip install ' + ' '.join(PIP_REQUIREMENTS))


def deploy():
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
    deploy()


if __name__ == '__main__':
    main()