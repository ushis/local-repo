# utils.py
# vim:ts=4:sw=4:noexpandtab

from sys import stderr, stdout
from time import gmtime, strftime

class LocalRepoError(Exception):
	''' Base exception used by all local-repo errors '''

	def __init__(self, msg):
		''' Sets the error message '''
		self._msg = msg

	@property
	def message(self):
		''' Returns the error message '''
		return self._msg

	def __str__(self):
		''' Returns the error message '''
		return self._msg


class Utils:
	''' Some simple utilities '''

	@staticmethod
	def is_number(val):
		''' Tests if an object is can be casted to int '''
		try:
			int(val)
			return True
		except:
			return False


class Msg:
	''' A simple class with some static methods for fancy colored output '''

	#: Color map
	COLORS = {'reset':    '\033[0m',
	          'black':    '\033[0;30m',
	          'red':      '\033[0;31m',
	          'green':    '\033[0;32m',
	          'yellow':   '\033[0;33m',
	          'blue':     '\033[0;34m',
	          'magenta':  '\033[0;35m',
	          'cyan':     '\033[0;36m',
	          'white':    '\033[0;37m',
	          'bblack':   '\033[1;30m',
	          'bred':     '\033[1;31m',
	          'bgreen':   '\033[1;32m',
	          'byellow':  '\033[1;33m',
	          'bblue':    '\033[1;34m',
	          'bmagenta': '\033[1;35m',
	          'bcyan':    '\033[1;36m',
	          'bwhite':   '\033[1;37m'}

	@staticmethod
	def colorize(msg, color):
		return Msg.COLORS[color] + msg + Msg.COLORS['reset']

	@staticmethod
	def msg(msg, color=None, stream=stdout):
		''' Prints a fancy colored message to a file stream '''
		msg = ' '.join((str(m) for m in msg)) if type(msg) is tuple else str(msg)

		if color:
			msg = Msg.colorize(msg, color)

		print(msg, file=stream)

	@staticmethod
	def process(*args):
		''' Prints process messages '''
		Msg.msg(('>',) + args, color='blue')

	@staticmethod
	def error(*args):
		''' Prints error messages '''
		Msg.msg(args, color='bred', stream=stderr)

	@staticmethod
	def result(*args):
		''' Prints result messages '''
		Msg.msg(args, color='bblue')

	@staticmethod
	def info(*args):
		''' Prints info messages '''
		Msg.msg(args)

	@staticmethod
	def ask(*args):
		''' Performs a simple yes/no question '''
		a = input(' '.join(args) + ' ' + _('[y|N]') + ' ')
		return a.lower() in [_('y'), _('yes')]

	@staticmethod
	def progress(read, size, total):
		''' Displays a simple progress bar '''
		read *= size
		p = min(0 if read < 1 or total < 1 else round(read / total * 100), 100)
		print('[{0:25}] {1}%'.format(round(p / 4) * '=', p), end = '\r' if read < total else '\n')

class Humanizer:
	''' A collection of methods converting data into human readable strings '''

	#: Translations
	TRANS = {'arch':         _('Architecture'),
	         'bugs':         _('Bugs'),
	         'builddate':    _('Build Date'),
	         'csize':        _('Package size'),
	         'desc':         _('Description'),
	         'filename':     _('Filename'),
	         'isize':        _('Installed size'),
	         'last update':  _('Last update'),
	         'license':      _('License'),
	         'location':     _('Location'),
	         'md5sum':       _('MD5sum'),
	         'name':         _('Name'),
	         'packager':     _('Packager'),
	         'packages':     _('Packages'),
	         'pgpsig':       _('Signed'),
	         'sha256sum':    _('SHA256sum'),
	         'translations': _('Translations'),
	         'url':          _('URL'),
	         'version':      _('Version'),
	         'website':      _('Website')}

	@staticmethod
	def filesize(s):
		''' Turns a filesize in bytes into a human readable format '''
		nice = lambda s, unit: '{0} {1}'.format(round(s, 2), unit)

		for unit in ['bytes', 'KiB', 'MiB', 'GiB']:
			if s < 1024:
				return nice(s, unit)

			s /= 1024

		return nice(s, 'TiB')

	@staticmethod
	def date(t):
		''' Converts a unix timestamp into a human readable format '''
		return strftime('%a %d %b %Y %H:%M:%S %Z', gmtime(t))

	@staticmethod
	def info(info, colored=True):
		''' Turns a dict into a human readable info string '''
		max = 0
		nice = []

		for k, v in info.items():
			if type(v) is bool:
				v = _('Yes') if v else _('No')
			elif type(v) in (list, tuple):
				v = ' '.join((str(i) for i in v))
			elif v is None:
				v = '-'
			else:
				v = str(v)

			if 'size' in k and Utils.is_number(v):
				v = Humanizer.filesize(int(v))
			elif 'date' in k and Utils.is_number(v):
				v = Humanizer.date(int(v))

			try:
				k = Humanizer.TRANS[k]
			except:
				pass

			if colored:
				k = Msg.colorize(k, 'cyan')

			if len(k) > max:
				max = len(k)

			nice.append((k, v))

		return '\n'.join(('{0:{1}}  {2}'.format(k, max, v) for k, v in nice))
