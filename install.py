#!/usr/bin/env python
from contextlib import contextmanager
from datetime import datetime
import getpass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib import request

VIRTUALENV_ROOT = Path('/usr/lib/virtualenv')
TELLSTICKLOGGER_URL = 'git+https://github.com/e9wikner/tellsticklogger.git'
TELLSTICK_LOG_DIR = Path('/var/lib/tellsticklogger')
BUILD_PATH = Path('/tmp/telldus-temp')
TELLDUS_DAEMON_INIT = Path('/etc/init.d/telldusd')
SERVICES = 'tellstick_sensorlog homeassistant@homeassistant notify_reboot.timer'
BACKUP_DIR = 'backup/' + str(datetime.now().isoformat()).replace(':', '')


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


# TODO: not tested, remove if not needed later
def uncomment(*, filename, regex, backup_dir=BACKUP_DIR):
    pattern = re.compile(regex)

    with open(filename) as inputfile:
        inputtext= inputfile.read()

    backupfile = Path(backup_dir) / filename.lstrip('/')
    backupfile.write_text(inputtext)
    print('Backup: {} --> {}'.format(filename, backup_file))

    def yield_uncommented_lines():
        for line in inputtext.splitlines():
            beginning, _, end = line.partition('#')
            if '' == beginning.strip() and pattern.search(end):
                yield beginning + end
            else:
                yield line

    print('Uncomment {} with regex {}'.format(filename, regex))
    newfile = Path(filename)
    newfile.write_text('\n'.join(yield_uncommented_lines()))


def setup_notifications():
    run('apt install ssmtp mailutils -yq')
    email_to = input('Email address that should receive notifications: ')
    email_from = input('Email address that should send notifications: ')
    mailhub = input('Email host? e.g. smtp.gmail.com:587: ')
    username = input('Email username:')
    password = getpass.getpass()

    ssmtp_conf = (
        "root=" + email_from,
        "mailhub=" + mailhub,
        # "rewriteDomain=" + 
        "hostname=localhost.localdomain",
        "UseTLS=Yes",
        "UseSTARTTLS=Yes",
        "AuthUser=" + username,
        "AuthPass=" + password)

    Path('/etc/ssmtp/ssmtp.conf').write_text('\n'.join(ssmtp_conf))
    Path('/etc/systemd/system/notify.conf').write_text('NOTIFY_EMAIL=' + email_to)


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
    shutil.rmtree(str(BUILD_PATH), ignore_errors=True)
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


def useradd(user, groups=None):
    try:
        run('useradd -rm {}'.format(user))
    except subprocess.CalledProcessError as error:
        if 9 == error.returncode:
            print(user + ' already exists')
        else:
            raise
    if groups:
        run('usermod --groups {} {}'.format(groups, user))


def setup_tellsticklogger():
    """ Create a virtual environment and install required packages"""
    user = 'telldus'
    run('useradd -rm {}'.format(user))
    setup_telldus()
    create_virtualenv(user, TELLSTICKLOGGER_URL)


def setup_homeassistant():
    """Create a virtual environment and install packages"""
    user = 'homeassistant'
    useradd(user, groups='dialout,gpio')
    create_virtualenv(user, user)
    run('{}/homeassistant/bin/pip install wheel'.format(VIRTUALENV_ROOT))


def deploy():
    """Deploy scripts and services"""
    run('rsync --checksum --recursive -hv src/ / --backup-dir {}'.format(backup_dir))
    TELLSTICK_LOG_DIR.mkdir(exist_ok=True) 
    run("systemctl daemon-reload")
    run("chmod +x /usr/local/bin -R")

    run('{}/telldus/bin/pip install --upgrade {}'.format(VIRTUALENV_ROOT, TELLSTICKLOGGER_URL))
    run('{}/homeassistant/bin/pip install --upgrade homeassistant'.format(VIRTUALENV_ROOT))

    # run('mkdir -p .plotly')
    # put('~/.plotly/.credentials', '~/.plotly/.credentials')
    # run('mkdir -p /var/lib/tellsticklogger')

    # TODO:
    #      >>> import plotly.tools as tls
    #      >>> tls.set_credentials_file(username='username', api_key='api-key')


def start():
    """Startup tellsticklogger and homeassistant"""
    shutil.chown(TELLSTICK_LOG_DIR, user='telldus', group='telldus')
    run("systemctl start " + SERVICES)
    run("systemctl enable " + SERVICES)


def cleanup():
    shutil.rmtree(str(BUILD_PATH), ignore_errors=True)


def main():
    os.makedirs(BACKUP_DIR)
    VIRTUALENV_ROOT.mkdir(exist_ok=True)
    setup_notifications()
    setup_tellsticklogger()
    setup_homeassistant()
    deploy()
    start()
    print('Setup is finished and homeassistant is launching at localhost:8123')
    cleanup()


if __name__ == '__main__':
    main()
