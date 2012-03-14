# package.py
# vim:ts=4:sw=4:noexpandtab

from os import listdir, remove, stat
from os.path import abspath, basename, dirname, isfile, isdir, join
from subprocess import call
from hashlib import md5, sha256
from urllib.request import urlretrieve
from tempfile import mkdtemp

import shutil
import tarfile
import re

from localrepo.pacman import Pacman
from localrepo.parser import PkgbuildParser, PkginfoParser
from localrepo.msg import Msg

class DependencyError(Exception):
	''' Handles missing dependencies '''

	def __init__(self, pkgbuild, deps):
		''' Sets the path to the pkgbuild and the deps '''
		self._pkgbuild = pkgbuild
		self._deps = deps

	@property
	def pkgbuild(self):
		''' Return the path to the pkgbuild '''
		return self._pkgbuild

	@property
	def deps(self):
		''' Returns the missing dependencies '''
		return self._deps

	def __str__(self):
		return _('Unresolved dependencies: {0}').format(', '.join(self._deps))

class Package:
	''' The package class provides static methods for building packages and
	an objectiv part to manage existing packages '''

	#: Package file extension
	EXT = '.pkg.tar.xz'

	#: PKGBUILD filename
	PKGBUILD = 'PKGBUILD'

	#: Path to a temporary directory
	tmpdir = None

	@staticmethod
	def get_tmpdir():
		''' Creates a temporary directory '''
		if Package.tmpdir is None or not isdir(Package.tmpdir):
			Package.tmpdir = mkdtemp('-local-repo')
		return Package.tmpdir

	@staticmethod
	def clean():
		''' Removes the temporary directory '''
		if Package.tmpdir is not None and isdir(Package.tmpdir):
			shutil.rmtree(Package.tmpdir)
		Package.tmpdir = None

	@staticmethod
	def from_remote_tarball(url):
		''' Downloads a remote tarball and forwards it to the package builder '''
		path = join(Package.get_tmpdir(), basename(url))

		try:
			urlretrieve(url, path)
		except:
			raise Exception(_('Could not download file: {0}').format(url))

		return Package.from_tarball(path)

	@staticmethod
	def from_tarball(path):
		''' Extracts a pkgbuild tarball and forward it to the package builder '''
		tmpdir = Package.get_tmpdir()
		path = abspath(path)

		if not isfile(path) or not tarfile.is_tarfile(path):
			raise Exception(_('File is no valid tarball: {0}').format(path))

		archive = tarfile.open(path)
		name = None

		for member in archive.getnames():
			if member.startswith('/') or member.startswith('..'):
				raise Exception(_('Tarball contains bad member: {0}').format(member))

			root = member.split('/')[0]

			if name is None:
				name = root
			elif name != root:
				raise Exception(_('Tarball contains multiple root directories'))

		archive.extractall(tmpdir)
		archive.close()
		return Package.from_pkgbuild(join(tmpdir, name))

	@staticmethod
	def from_pkgbuild(path, ignore_deps=False):
		''' Makes a package from a pkgbuild '''
		path = abspath(path)

		if basename(path) != Package.PKGBUILD:
			path = join(path, Package.PKGBUILD)

		if not isfile(path):
			raise IOError(_('Could not find file: {0}').format(path))

		info = PkgbuildParser(path).parse()

		if not ignore_deps:
			unresolved = Pacman.check_deps(info['depends'] + info['makedepends'])

			if unresolved:
				raise DependencyError(path, unresolved)

		path = dirname(path)
		Pacman.make_package(path)

		for f in listdir(path):
			if f.startswith('{0}'.format(info['name'])) and f.endswith(Package.EXT):
				return Package.from_file(join(path, f))

		raise IOError(_('Could not find any package'))

	@staticmethod
	def from_file(path):
		''' Creates a package object from a package file '''
		path = abspath(path)

		# AAAAARRRGG
		#
		# The current version of tarfile (0.9) does not support lzma compressed archives.
		# The next version will: http://hg.python.org/cpython/file/default/Lib/tarfile.py

		#if not isfile(path) or not tarfile.is_tarfile(path):
		#	raise Exception('File is not a valid package: {0}'.format(path))
		#
		#pkg = tarfile.open(path)
		#
		#try:
		#	pkginfo = pkg.extractfile('.PKGINFO').read().decode('utf8')
		#except:
		#	raise Exception('File is not valid package: {0}'.format(path))
		#
		#pkg.close()

		# Begin workaround
		if not isfile(path):
			raise Exception(_('File does not exist: {0}').format(path))

		tmpdir = Package.get_tmpdir()

		if call(['tar', '-xJf', path, '-C', tmpdir, '.PKGINFO']) is not 0:
			raise Exception(_('An error occurred in tar'))

		pkginfo = open(join(tmpdir, '.PKGINFO')).read()
		# End workaround

		info = PkginfoParser(pkginfo).parse()
		info['csize'] = stat(path).st_size
		data = open(path, 'rb').read()
		info['md5sum'] = md5(data).hexdigest()
		info['sha256sum'] = sha256(data).hexdigest()
		return Package(info['name'], info['version'], path, info)

	@staticmethod
	def forge(path):
		''' Forwards the path to an package builder '''
		if re.match('(?:http(?:s)?|ftp)://', path) is not None:
			return Package.from_remote_tarball(path)

		if path.endswith('.tar.gz'):
			return Package.from_tarball(path)

		if basename(path) == Package.PKGBUILD:
			return Package.from_pkgbuild(path)

		if path.endswith(Package.EXT):
			return Package.from_file(path)

		raise Exception(_('Invalid file name: {0}').format(path))

	def __init__(self, name, version, path, infos=None):
		''' Creates new package object, additional package infos must be a dict '''
		self._name = name
		self._version = version
		self._filename = basename(path)
		self._path = abspath(path)
		self._infos = {} if infos is None else infos

	@property
	def name(self):
		''' Returns the package name '''
		return self._name

	@property
	def version(self):
		''' Return the package vesion '''
		return self._version

	@property
	def path(self):
		''' Return absolute the path to the package '''
		return self._path

	@property
	def infos(self):
		''' Returns package infos '''
		infos = self._infos
		infos['name'] = self._name
		infos['version'] = self._version
		infos['filename'] = self._filename
		return infos

	@property
	def has_valid_sha256sum(self):
		''' Compares the checksum of the package file with the sum in the info dict '''
		if not 'sha256sum' in self._infos:
			return False

		try:
			data = open(self._path, 'rb').read()
			return sha256(data).hexdigest() == self._infos['sha256sum']
		except:
			return False

	def move(self, path, force=False):
		''' Moves the package to a new location '''
		path = abspath(path)

		if not isdir(path):
			raise Exception(_('Destination is no directory: {0}').format(path))

		path = join(path, self._filename)

		if self._path == path:
			return

		if not force and isfile(path):
			raise Exception(_('File already exists: {0}').format(path))

		shutil.move(self._path, path)
		self._path = path

	def remove(self):
		''' Removes the package file '''
		if isfile(self._path):
			remove(self._path)

	def __str__(self):
		return Msg.human_infos(self.infos)
