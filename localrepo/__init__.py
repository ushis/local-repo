# __init__.py
# vim:ts=4:sw=4:noexpandtab

from os.path import dirname, exists, join, pardir

import builtins
import gettext

__all__ = ['aur', 'config', 'log', 'package', 'pacman', 'parser', 'repo', 'utils']

def find_base():
	d = dirname(dirname(__file__))

	while not exists(join(d, 'local-repo')) and not exists(join(d, 'bin', 'local-repo')):
		d = join(d, pardir)

		if not exists(d):
			raise Exception('Could not find basepath')

	return d

BASE = find_base()

gettext.bindtextdomain('localrepo', join(BASE, 'share', 'locale'))
gettext.textdomain('localrepo')
builtins._ = gettext.gettext
