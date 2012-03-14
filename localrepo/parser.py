# parser.py
# vim:ts=4:sw=4:noexpandtab

from re import findall, match, search, split
from subprocess import check_output

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
		cmd = '. {0} '.format(self._data)
		cmd += ' '.join(['&& echo "{0}=${{{0}[@]}}"'.format(k) for k in PkgbuildParser.TRANS])

		try:
			data = check_output([cmd], shell=True).decode('utf8')
		except:
			raise ParserError(_('Could not parse PKGBUILD: {0}').format(self._data))

		data = dict(findall('([a-z]+)=([^\n]*)\n', data))
		info = {}

		for k in PkgbuildParser.TRANS:
			try:
				val = data[k]
			except KeyError:
				raise ParserError(_('Could not parse PKGBUILD: {0}').format(self._data))

			if type(PkgbuildParser.TRANS[k]) is list:
				info[k] = val.split(' ') if val != '' else []
				continue

			if val == '':
				raise ParserError(_('Missing PKGBUILD entry: {0}').format(k))

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
			return {t: info[k] for k, t in PkginfoParser.TRANS.items()}
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
