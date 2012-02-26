#!/usr/bin/env python3.2

from os.path import abspath, dirname, exists, join, pardir

import builtins
import gettext

__all__ = ['aur', 'msg', 'package', 'repo']

dev_path = join(abspath(dirname(__file__)), pardir)

if exists(join(dev_path, 'setup.py')):
	gettext.bindtextdomain('localrepo', join(dev_path, 'share', 'locale'))

gettext.textdomain('localrepo')
builtins._ = gettext.gettext
