#!/usr/bin/env python3.2
# vim:ts=4:sw=4:noexpandtab

from distutils.core import setup
from os.path import join, isfile
from subprocess import call
from glob import glob

if call([join('share', 'po.sh'), 'compile']) is not 0:
	print('Language compiling failed')
	exit(1)

msg = glob(join('share', 'locale', '*', 'LC_MESSAGES'))
f = 'localrepo.mo'

setup(name='local-repo',
      version='1.5',
      description='Arch Linux local repository manager',
      author='ushi',
      author_email='ushi@porkbox.net',
      url='https://github.com/ushis/local-repo',
      scripts=['local-repo'],
      packages=['localrepo'],
      data_files=[(d, [join(d, f)]) for d in msg if isfile(join(d, f))])
