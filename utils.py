#!/usr/bin/env python
from contextlib import contextmanager
import os
import subprocess


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