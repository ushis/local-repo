#!/usr/bin/env python3.2

from os.path import abspath, dirname, exists, join, pardir

import builtins
import gettext

__all__ = ['aur', 'msg', 'package', 'repo']

def find_base():
	d = join(abspath(dirname(__file__)), pardir)

	while not exists(join(d, 'local-repo')) and not exists(join(d, 'bin', 'local-repo')):
		d = join(d, pardir)

		if not exists(d):
			raise Exception('Could find basepath')

	return d

BASE = find_base()

gettext.bindtextdomain('localrepo', join(BASE, 'share', 'locale'))
gettext.textdomain('localrepo')
builtins._ = gettext.gettext
