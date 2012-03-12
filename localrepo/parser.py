# parser.py
# vim:ts=4:sw=4:noexpandtab

from re import findall, search, split

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

	def parse(self):
		''' Parses a PKGBUILD '''
		info = dict(findall('({0})=([^\n]+)\n'.format('|'.join(PkgbuildParser.TRANS)), self._data))

		try:
			info = {PkgbuildParser.TRANS[k]: info[k] for k in PkgbuildParser.TRANS}
		except:
			raise ParserError(_('Invalid PKGBUILD'))

		info['depends'] = self._find_deps()
		return self._clean_values(info)

	def _find_deps(self):
		''' Finds dependencies '''
		deps = findall('(?<!opt)depends=\(([^\)]+)\)', self._data)

		if not deps:
			return []

		return [d for dl in (split('\s+', dl) for dl in deps) for d in dl]

	def _clean_values(self, data):
		''' Recursively strips quotes from dict/list values and strings and replaces bash vars'''
		if type(data) is str:
			data = data.strip('\'"')

			# This var replacement is not very safe! It works for $var and ${var}, but no
			# super fancy structures like arrays and stuff...
			var = findall('(\$(?:{)?([^\s}]+)(?:})?)', data)

			if not var:
				return data

			for v in var:
				val = search('{0}=([^\n]+)\n'.format(v[1]), self._data)

				if val is not None:
					data = data.replace(v[0], val.group(1))

			return data

		if type(data) is list:
			return [self._clean_values(v) for v in data]

		if type(data) is dict:
			return {k: self._clean_values(v) for k, v in data.items()}

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
