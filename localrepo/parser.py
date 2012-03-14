# parser.py
# vim:ts=4:sw=4:noexpandtab

from re import findall, match, search, split
from subprocess import check_output
from collections import deque

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
	         'pkgver': 'version',
			 'depends': [],
	         'makedepends': []}

	def parse(self):
		''' Parses a PKGBUILD - self._data must be the path to a PKGBUILD file'''
		keys = sorted(PkgbuildParser.TRANS)
		cmd = '. {0} '.format(self._data)
		cmd += ' '.join(['&& echo "${{{0}[@]}}"'.format(k) for k in keys])

		try:
			res = deque(check_output([cmd], shell=True).decode('utf8').split('\n'))
		except:
			raise ParserError(_('Invalid PKGBUILD'))

		info = {}

		for k in keys:
			try:
				val = res.popleft()
			except:
				raise ParserError(_('Invalid PKGBUILD'))

			if type(PkgbuildParser.TRANS[k]) is list:
				info[k] = val.split(' ') if val != '' else []
				continue

			if val == '':
				raise ParserError(_('Invalid PKGBUILD'))

			info[PkgbuildParser.TRANS[k]] = val

		return info


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
