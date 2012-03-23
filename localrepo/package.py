# package.py
# vim:ts=4:sw=4:noexpandtab

from os import listdir, remove, stat
from os.path import abspath, basename, dirname, isabs, isfile, isdir, join, normpath
from shutil import copytree, move, rmtree
from subprocess import call
from hashlib import md5, sha256
from urllib.request import urlretrieve
from tempfile import mkdtemp
from tarfile import is_tarfile, open as open_tarfile
from distutils.version import LooseVersion

from localrepo.pacman import Pacman, PacmanError
from localrepo.parser import PkgbuildParser, PkginfoParser
from localrepo.utils import Humanizer, LocalRepoError, Msg
from localrepo.config import Config
from localrepo.log import BuildLog, PkgbuildLog

class PackageError(LocalRepoError):
	''' Handles package errors '''
	pass


class BuildError(PackageError):
	''' Handles build errors '''
	pass


class DependencyError(PackageError):
	''' Handles missing dependencies '''

	def __init__(self, pkgbuild, deps):
		''' Sets the path to the pkgbuild and the deps '''
		super().__init__(_('Unresolved dependencies: {0}').format(', '.join(deps)))
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


class Package:
	''' The package class provides static methods for building packages and
	an objectiv part to manage existing packages '''

	#: Package file extensions
	EXT = ('.pkg.tar', '.pkg.tar.gz', '.pkg.tar.bz2', '.pkg.tar.xz')
	# '.pkg.tar.Z' would also be possible, but it's not supported by tarfile

	#: Tarball extensions
	TARBALLEXT = ('.tar', '.tar.gz', '.tar.bz2')

	#: PKGINFO filename
	PKGINFO = '.PKGINFO'

	#: PKGBUILD filename
	PKGBUILD = 'PKGBUILD'

	#: Log file extension
	LOGEXT = '.log'

	#: Path to a temporary directory
	tmpdir = None

	@staticmethod
	def get_tmpdir():
		''' Creates a temporary directory '''
		if Package.tmpdir is None or not isdir(Package.tmpdir):
			Package.tmpdir = mkdtemp(prefix='local-repo-')
		return Package.tmpdir

	@staticmethod
	def clean():
		''' Removes the temporary directory '''
		if Package.tmpdir is not None and isdir(Package.tmpdir):
			rmtree(Package.tmpdir)
		Package.tmpdir = None

	@staticmethod
	def from_remote_file(url):
		''' Downloads a remote tarball and forwards it to the package builder '''
		path = join(Package.get_tmpdir(), basename(url))

		try:
			urlretrieve(url, path, reporthook=Msg.progress)
		except:
			raise BuildError(_('Could not download file: {0}').format(url))

		return Package.forge(path)

	@staticmethod
	def from_tarball(path):
		''' Extracts a pkgbuild tarball and forward it to the package builder '''
		path = abspath(path)

		try:
			archive = open_tarfile(path)
		except:
			raise BuildError(_('Could not open tarball: {0}').format(path))

		tmpdir = Package.get_tmpdir()
		root = None

		for member in archive.getmembers():
			if isabs(member.name) or not normpath(join(tmpdir, member.name)).startswith(tmpdir):
				raise BuildError(_('Tarball contains bad member: {0}').format(member.name))

			if root is False:
				continue

			name = normpath(member.name)
			_root = name.split('/')[0]

			if member.isfile() and _root == name:
				root = False
			elif root is None:
				root = _root
			elif root != _root:
				root = False

		if not root:
			tmpdir = mkdtemp(dir=tmpdir)

		try:
			archive.extractall(tmpdir)
			archive.close()
		except:
			raise BuildError(_('Could not extract tarball: {0}').format(path))

		return Package.from_pkgbuild(join(tmpdir, root) if root else tmpdir)

	@staticmethod
	def _load_pkgbuild(name, path):
		''' Stores the PKGBUILD dir or loads an existing PKGBUILD from the pkgbuild dir '''
		if not path.startswith(PkgbuildLog.log_dir(name)):
			PkgbuildLog.store(name, path)
			return path

		try:
			tmpdir = join(mkdtemp(dir=Package.get_tmpdir()), name)
			copytree(path, tmpdir)
			return tmpdir
		except:
			raise BuildError(_('Could not load PKGBUILD into workspace: {0}').format(path))

	@staticmethod
	def from_pkgbuild(path, ignore_deps=False):
		''' Makes a package from a pkgbuild '''
		path = abspath(path)

		if basename(path) != Package.PKGBUILD:
			path = join(path, Package.PKGBUILD)

		if not isfile(path):
			raise BuildError(_('Could not find PKGBUILD: {0}').format(path))

		info = PkgbuildParser(path).parse()

		if not ignore_deps:
			unresolved = Pacman.check_deps(info['depends'] + info['makedepends'])

			if unresolved:
				raise DependencyError(path, unresolved)

		path = dirname(path)
		log = bool(Config.get('buildlog', False))

		if Config.get('pkgbuild', False):
			path = Package._load_pkgbuild(info['name'], path)

		try:
			Pacman.make_package(path, log=log)
		except PacmanError as e:
			raise e
		finally:
			pkgfile = None

			for f in (f for f in listdir(path) if f.startswith(info['name'])):
				if log and f.endswith(Package.LOGEXT):
					BuildLog.store(info['name'], join(path, f))
				elif f.endswith(Package.EXT):
					pkgfile = f

		if pkgfile:
			return Package.from_file(join(path, pkgfile))

		raise BuildError(_('Could not find any package'))

	@staticmethod
	def from_file(path):
		''' Creates a package object from a package file '''
		path = abspath(path)

		# AAAAARRRGG
		#
		# The current version of tarfile (0.9) does not support lzma compressed archives.
		# The next version will: http://hg.python.org/cpython/file/default/Lib/tarfile.py

		#try:
		#	pkg = open_tarfile(path)
		#except:
		#	raise BuildError(_('Could not open package: {0}').format(path))
		#
		#try:
		#	pkginfo = pkg.extractfile('.PKGINFO').read().decode('utf8')
		#except:
		#	raise BuildError(_('Could not read package info: {0}').format(path))
		#finally:
		#	pkg.close()

		# Begin workaround
		if not isfile(path):
			raise BuildError(_('File does not exist: {0}').format(path))

		if is_tarfile(path):
			pkg = open_tarfile(path)

			try:
				pkginfo = pkg.extractfile(Package.PKGINFO).read().decode('utf8')
			except:
				raise BuildError(_('Could not read package info: {0}').format(path))
			finally:
				pkg.close()
		else:
			# Handling lzma compressed archives (.pkg.tar.xz)
			tmpdir = Package.get_tmpdir()

			if call(['tar', '-xJf', path, '-C', tmpdir, Package.PKGINFO]) is not 0:
				raise BuildError(_('An error occurred in tar'))

			pkginfo = open(join(tmpdir, Package.PKGINFO)).read()
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
		if path.startswith(('http://', 'https://', 'ftp://')):
			return Package.from_remote_file(path)

		if path.endswith(Package.EXT):
			return Package.from_file(path)

		if basename(path) == Package.PKGBUILD or isdir(path):
			return Package.from_pkgbuild(path)

		if path.endswith(Package.TARBALLEXT):
			return Package.from_tarball(path)

		raise BuildError(_('Invalid file name: {0}').format(path))

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

	def has_smaller_version_than(self, version):
		''' Compares the current package version with another one '''
		try:
			return LooseVersion(self._version) < LooseVersion(version)
		except:
			return self._version < version

	def move(self, path, force=False):
		''' Moves the package to a new location '''
		path = abspath(path)

		if not isdir(path):
			raise Package(_('Destination is no directory: {0}').format(path))

		path = join(path, self._filename)

		if self._path == path:
			return

		if not force and isfile(path):
			raise PackageError(_('File already exists: {0}').format(path))

		move(self._path, path)
		self._path = path

	def remove(self):
		''' Removes the package file '''
		if isfile(self._path):
			remove(self._path)

	def __str__(self):
		return Humanizer.info(self.infos)
