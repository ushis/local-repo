# package.py
# vim:ts=4:sw=4:noexpandtab

from os import listdir, remove
from os.path import abspath, basename, dirname, getsize, isabs, isfile, isdir, join, normpath
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

	#: Signature file extension
	SIGEXT = '.sig'

	#: VCS suffixes
	VCS = ('-git', '-cvs', '-svn', '-hg', '-darcs', '-bzr')

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
	def from_remote_file(url, force=False):
		''' Downloads a remote tarball and forwards it to the package builder '''
		path = join(Package.get_tmpdir(), basename(url))

		try:
			urlretrieve(url, path, reporthook=Msg.progress)
		except:
			raise BuildError(_('Could not download file: {0}').format(url))

		return Package.forge(path, force=force)

	@staticmethod
	def from_tarball(path, force=False):
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

		return Package.from_pkgbuild(join(tmpdir, root) if root else tmpdir, force=force)

	@staticmethod
	def _process_pkgbuild(path):
		''' Parses the PKGBUILD and stores or loads it in/from the pkgbuild dir '''
		info = PkgbuildParser(path).parse()
		path = dirname(path)

		if not Config.get('pkgbuild', False):
			return path, info

		if not path.startswith(PkgbuildLog.log_dir(info['name'])):
			PkgbuildLog.store(info['name'], path)
			return path, info

		tmpdir = join(Package.get_tmpdir(), info['name'])
		PkgbuildLog.load(info['name'], tmpdir)
		return tmpdir, info

	@staticmethod
	def _process_build_output(name, path):
		''' Stores buildlogs and finds the package file '''
		try:
			files = (f for f in listdir(path) if f.startswith(name))
		except OSError:
			raise BuildError(_('Could not list directory: {0}').format(path))

		pkgfile = None
		log = Config.get('buildlog', False)

		for f in files:
			if log and f.endswith(Package.LOGEXT):
				BuildLog.store(name, join(path, f))
			elif f.endswith(Package.EXT):
				pkgfile = f

		return pkgfile

	@staticmethod
	def from_pkgbuild(path, ignore_deps=False, force=False):
		''' Makes a package from a pkgbuild '''
		path = abspath(path)

		if basename(path) != Package.PKGBUILD:
			path = join(path, Package.PKGBUILD)

		if not isfile(path):
			raise BuildError(_('Could not find PKGBUILD: {0}').format(path))

		path, info = Package._process_pkgbuild(path)

		if not ignore_deps:
			unresolved = Pacman.check_deps(info['depends'] + info['makedepends'])

			if unresolved:
				raise DependencyError(path, unresolved)

		try:
			Pacman.make_package(path, force=force)
		except PacmanError as e:
			raise e
		finally:
			pkgfile = Package._process_build_output(info['name'], path)

		if pkgfile:
			return Package.from_file(join(path, pkgfile))

		raise BuildError(_('Could not find any package: {0}').format(path))

	@staticmethod
	def from_file(path):
		''' Creates a package object from a package file '''
		path = abspath(path)

		try:
			pkg = open_tarfile(path)
		except:
			raise BuildError(_('Could not open package: {0}').format(path))

		try:
			pkginfo = pkg.extractfile('.PKGINFO').read().decode('utf8')
		except:
			raise BuildError(_('Could not read package info: {0}').format(path))
		finally:
			pkg.close()

		info = PkginfoParser(pkginfo).parse()
		info['pgpsig'] = isfile(path + Package.SIGEXT)

		try:
			info['csize'] = getsize(path)
			data = open(path, 'rb').read()
			info['md5sum'] = md5(data).hexdigest()
			info['sha256sum'] = sha256(data).hexdigest()
		except OSError:
			raise BuildError(_('Could not determine package size: {0}').format(path))
		except:
			raise BuildError(_('Could not calculate package checksums: {0}').format(path))

		return Package(info['name'], info['version'], path, info)

	@staticmethod
	def forge(path, force=False):
		''' Forwards the path to an package builder '''
		if path.startswith(('http://', 'https://', 'ftp://')):
			return Package.from_remote_file(path, force=force)

		if path.endswith(Package.EXT):
			return Package.from_file(path)

		if basename(path) == Package.PKGBUILD or isdir(path):
			return Package.from_pkgbuild(path, force=force)

		if path.endswith(Package.TARBALLEXT):
			return Package.from_tarball(path, force=force)

		raise BuildError(_('Invalid file name: {0}').format(path))

	def __init__(self, name, version, path, info):
		''' Creates new package object, additional package infos must be a dict '''
		self._name = name
		self._version = version
		self._filename = basename(path)
		self._path = abspath(path)
		self._sigfile = self._path + Package.SIGEXT
		self._info = info

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
	def sigfile(self):
		''' Returns the path to the signature file '''
		return self._sigfile

	@property
	def is_signed(self):
		''' Am I signed? '''
		try:
			return bool(self._info['pgpsig'])
		except:
			return False

	@property
	def info(self):
		''' Returns package infos '''
		info = self._info
		info['name'] = self._name
		info['version'] = self._version
		info['filename'] = self._filename
		return info

	def __eq__(self, other):
		''' Two packages are equal, if they have the same path '''
		return self._path == other.path

	def __ne__(self, other):
		''' Two packages are not equal, if they have different paths '''
		return self._path != other.path

	@property
	def has_valid_sha256sum(self):
		''' Compares the checksum of the package file with the sum in the info dict '''
		try:
			if self._info['sha256sum'] is None:
				return False

			data = open(self._path, 'rb').read()
			return sha256(data).hexdigest() == self._info['sha256sum']
		except:
			return False

	@property
	def is_vcs(self):
		''' Am i a vcs package? '''
		return self._name.endswith(Package.VCS)

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
			raise PackageError(_('Destination is no directory: {0}').format(path))

		path = join(path, self._filename)

		if self._path == path:
			return

		if not force and isfile(path):
			raise PackageError(_('File already exists: {0}').format(path))

		try:
			move(self._path, path)
			self._path = path
		except:
			raise PackageError(_('Could not move package: {0} -> {1}').format(self._path, path))

		if not self.is_signed:
			return

		path += Package.SIGEXT

		try:
			move(self._sigfile, path)
			self._sigfile = path
		except:
			raise PackageError(_('Could not move sig file: {0} -> {1}').format(self._sigfile, path))

	def remove(self):
		''' Removes the package file '''
		try:
			if isfile(self._path):
				remove(self._path)

			if isfile(self._sigfile):
				remove(self._sigfile)
		except:
			raise PackageError(_('Could not remove package: {0}').format(self._path))

	def __str__(self):
		return Humanizer.info(self.info)
