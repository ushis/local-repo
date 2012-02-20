#!/usr/bin/env python3.2

from distutils.core import setup

setup(name='local-repo',
      version='1.0',
	  description='Arch Linux local repository manager',
	  author='ushi',
	  author_email='ushi@porkbox.net',
	  url='https://github.com/ushis/local-repo',
	  scripts=['local-repo'],
	  packages=['localrepo'])
