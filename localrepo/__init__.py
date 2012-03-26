# __init__.py
# vim:ts=4:sw=4:noexpandtab

import builtins

from os.path import dirname, exists, join
from gettext import bindtextdomain, textdomain, gettext

__all__ = ['aur', 'config', 'log', 'package', 'pacman', 'parser', 'repo', 'utils']

locale = join(dirname(dirname(__file__)), 'share', 'locale')

if not exists(locale):
	locale = '/usr/share/locale'

bindtextdomain('localrepo', locale)
textdomain('localrepo')
builtins._ = gettext
