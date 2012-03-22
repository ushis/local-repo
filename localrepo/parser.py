# parser.py
# vim:ts=4:sw=4:noexpandtab

from re import compile as compile_pattern
from subprocess import check_output

from localrepo.utils import LocalRepoError

class ParserError(LocalRepoError):
	''' Handles parser errors '''
	pass


class Parser:
	''' The base parser class '''

	def __init__(self, data):
		''' Sets the data string '''
		self._data = data

	def parse(self):
		''' Must be implemented in the child classes. Do not use this class directly.'''
		raise NotImplementedError('Must be implemented in the child class')


class PkgbuildParser(Parser):
	''' The PKGBUILD parser '''

	#: Pattern matches 'key=val'
	PATTERN = compile_pattern('([a-z]+)=([^\n]*)\n')

	#: Translations from PKGBUILD to local-repo
	TRANS = {'pkgname': 'name',
	         'pkgver': 'version',
	         'depends': list,
	         'makedepends': list}

	#: Bash command that prints needed info 'key=val' style
	ECHO = ' && '.join(('echo "{0}=${{{0}[@]}}"'.format(k) for k in TRANS))

	def parse(self):
		''' Parses a PKGBUILD - self._data must be the path to a PKGBUILD file'''
		cmd = 'source {0} && {1}'.format(self._data, PkgbuildParser.ECHO)

		try:
			data = check_output(['/bin/bash', '-c', cmd]).decode('utf8')
		except:
			raise ParserError(_('Could not parse PKGBUILD: {0}').format(self._data))

		data = dict(PkgbuildParser.PATTERN.findall(data))
		info = {}

		for k, t in PkgbuildParser.TRANS.items():
			if k not in data:
				raise ParserError(_('Could not parse PKGBUILD: {0}').format(self._data))

			if t is list:
				info[k] = data[k].split(' ') if data[k] != '' else []
			elif data[k] != '':
				info[t] = data[k]
			else:
				raise ParserError(_('Missing PKGBUILD entry: {0}').format(k))

		return info


class PkginfoParser(Parser):
	''' The PKGINFO parser '''

	#: Pattern matches 'key = val'
	PATTERN = compile_pattern('([a-z]+) = ([^\n]+)\n')

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
		info = dict(PkginfoParser.PATTERN.findall(self._data))

		try:
			return {t: info[k] for k, t in PkginfoParser.TRANS.items()}
		except KeyError as e:
			raise ParserError(_('Missing PKGINFO entry: {0}').format(e))


class DescParser(Parser):
	''' The database desc parser '''

	#: Pattern matches '%key%\nval'
	PATTERN = compile_pattern('%([A-Z256]+)%\n([^\n]+)\n')

	#: List of mandatory fields
	MANDATORY = ['filename', 'name', 'version', 'desc', 'csize', 'isize', 'md5sum',
	             'sha256sum', 'url', 'license', 'arch', 'builddate', 'packager']

	def parse(self):
		''' Parses a desc file '''
		info = {k.lower(): v for k, v in DescParser.PATTERN.findall(self._data)}
		missing = [field for field in DescParser.MANDATORY if field not in info]

		if missing:
			raise ParserError(_('Missing fields: {0}').format(', '.join(missing)))

		return info
