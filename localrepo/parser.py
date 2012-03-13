# parser.py
# vim:ts=4:sw=4:noexpandtab

from re import findall, match, search, split
from collections import deque
import shlex

class ParserError(Exception):
	''' Exception handles parser errors '''

	def __init__(self, msg):
		self._msg = msg

	@property
	def message(self):
		''' Returns the error messages '''
		return self._msg

	def __str__(self):
		''' Return the error messages '''
		return self._msg


class Parser:
	''' The base parser class '''

	def __init__(self, data):
		''' Sets the data string '''
		self._data = data

	def parse(self):
		''' Must be implemented in the child classes.
		Do not use this class directly.'''
		raise NotImplementedError('Must be implemented in the child class')


class PkgbuildParser(Parser):
	''' The PKGBUILD parser '''

	#: Translations from PKGBUILD to local-repo
	TRANS = {'pkgname': 'name',
	         'pkgver': 'version'}

	#: Needed dependencies
	DEPENDS = ['depends', 'makedepends']

	def parse(self):
		''' Parses a PKGBUILD '''
		tokens = deque(shlex.split(self._data))
		self._symbols = {}

		while tokens:
			token = tokens.popleft()

			# Skip functions
			if token == '{':
				while token != '}' and tokens:
					token = tokens.popleft()
				continue

			# Skip non assigments
			if not match('^[a-zA-Z0-9_]+=', token):
				continue

			var, eq, val = token.partition('=')

			# Handle arrays
			if val.startswith('('):
				self._symbols[var] = []
				val = val[1:]

				while not val.endswith(')') and tokens:
					self._symbols[var].append(self._substitute(val))
					val = tokens.popleft()

				self._symbols[var].append(self._substitute(val[:-1]))
			else:
				self._symbols[var] = self._substitute(val)

		try:
			info = {PkgbuildParser.TRANS[k]: self._symbols[k] for k in PkgbuildParser.TRANS}
		except KeyError:
			raise ParserError(_('Invalid PKGBUILD'))

		info['depends'] = []

		for deps in (deps for deps in PkgbuildParser.DEPENDS if deps in self._symbols):
			info['depends'] += self._symbols[deps]

		return info

	def _substitute(self, v):
		''' Substitutes vars in values with their values  '''
		m = search('\$(?:{)?([^\s}]+)(?:})?', v)

		if not m:
			return v

		try:
			return v.replace(m.group(0), self._symbols[m.group(1)])
		except KeyError:
			return ''


class PkginfoParser(Parser):
	''' The PKGINFO parser '''

	#: Translations from PKGINFO to local-repo
	TRANS = {'pkgname': 'name',
	         'pkgver': 'version',
	         'pkgdesc': 'desc',
	         'size': 'isize',
	         'url': 'url',
	         'license': 'license',
	         'arch': 'arch',
	         'builddate': 'builddate',
	         'packager': 'packager'}

	def parse(self):
		''' Parses a PKGINFO '''
		info = dict(findall('([a-z]+) = ([^\n]+)\n', self._data))

		try:
			return {PkginfoParser.TRANS[k]: info[k] for k in PkginfoParser.TRANS}
		except:
			raise ParserError(_('Invalid .PKGINFO'))


class DescParser(Parser):
	''' The database desc parser '''

	#: List of mandatory fields
	MANDATORY = ['filename', 'name', 'version', 'desc', 'csize', 'isize', 'md5sum',
	             'sha256sum', 'url', 'license', 'arch', 'builddate', 'packager']

	def parse(self):
		''' Parses a desc file '''
		info = {k.lower(): v for k, v in findall('%([A-Z256]+)%\n([^\n]+)\n', self._data)}

		if any(True for field in DescParser.MANDATORY if field not in info):
			raise ParserError(_('Invalid database entry'))

		return info
