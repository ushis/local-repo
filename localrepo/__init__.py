# __init__.py
# vim:ts=4:sw=4:noexpandtab

import builtins

from os.path import dirname, exists, join, pardir
from gettext import bindtextdomain, textdomain, gettext

__all__ = ['aur', 'config', 'log', 'package', 'pacman', 'parser', 'repo', 'utils']

def find_locale():
	d = dirname(dirname(__file__))

	while not exists(join(d, 'share', 'locale')):
		d = join(d, pardir)

		if not exists(d):
			raise Exception('Could not find basepath')

	return join(d, 'share', 'locale')

bindtextdomain('localrepo', find_locale())
textdomain('localrepo')
builtins._ = gettext
