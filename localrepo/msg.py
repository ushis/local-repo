# msg.py
# vim:ts=4:sw=4:noexpandtab

import re
import sys
import time

class Msg:
	''' A simple class with some static methods for fancy colored output '''

	@staticmethod
	def process(*args):
		''' Prints yellow bold process messages '''
		print('\033[0;34m>', ' '.join(args), '\033[0m')

	@staticmethod
	def error(*args):
		''' Prints red bold error messages '''
		print('\033[1;31m' + ' '.join(args), '\033[0m', file=sys.stderr);

	@staticmethod
	def result(*args):
		''' Prints blue bold result messages '''
		print('\033[1;34m' + ' '.join(args), '\033[0m')

	@staticmethod
	def info(*args):
		''' Prints info messages '''
		print(' '.join(args))

	@staticmethod
	def yes(*args):
		''' Performs a simple yes/no question '''
		a = input(' '.join(args) + '? [y|N] ')
		return False if re.match('^y(?:es)?', a, flags=re.IGNORECASE) is None else True

	@staticmethod
	def is_int(i):
		''' Test a string for integer '''
		try:
			int(i)
			return True
		except:
			return False

	@staticmethod
	def human_fsize(s):
		''' Turns a filesize in bytes into a human readable format '''
		for unit in ['bytes', 'KiB', 'MiB', 'GiB']:
			if s < 1024:
				return '{0} {1}'.format(s, unit)
			s = round((s / 1024), 2)
		return '{0} {1}'.format(s, 'TiB')

	@staticmethod
	def human_date(t):
		''' Converts a unix timestamp into a human readable format '''
		return time.strftime('%a %d %b %Y %H:%M:%S %Z', time.gmtime(t))

	@staticmethod
	def human_infos(infos):
		''' Turns a dict into a human readable info string '''
		trans = {'arch':        _('Architecture'),
		         'builddate':   _('Build Date'),
		         'csize':       _('Package size'),
		         'desc':        _('Description'),
		         'filename':    _('Filename'),
		         'isize':       _('Installed size'),
		         'last update': _('Last update'),
		         'license':     _('License'),
		         'location':    _('Location'),
		         'md5sum':      _('MD5sum'),
		         'name':        _('Name'),
		         'packager':    _('Packager'),
		         'packages':    _('Packages'),
		         'sha256sum':   _('SHA256sum'),
		         'url':         _('URL'),
		         'version':     _('Version')}

		max = 0
		nice = []

		for k, v in infos.items():
			if 'size' in k and Msg.is_int(v):
				v = Msg.human_fsize(int(v))
			elif 'date' in k and Msg.is_int(v):
				v = Msg.human_date(int(v))

			if k in trans:
				k = trans[k]

			if len(k) > max:
				max = len(k)

			nice.append((k, v))

		return '\n'.join(('\033[0;36m{0:{1}}\033[0m  {2}'.format(k, max, v) for k, v in nice))
