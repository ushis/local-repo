# repo.py
# vim:ts=4:sw=4:noexpandtab

from os import listdir, makedirs, remove
from os.path import abspath, basename, dirname, getctime, isabs, isdir, isfile, join, normpath, splitext
from tarfile import open as open_tarfile
from pickle import dump as pickle, load as unpickle

from localrepo.pacman import Pacman, PacmanError
from localrepo.package import Package
from localrepo.parser import DescParser, ParserError
from localrepo.utils import Humanizer, LocalRepoError
from localrepo.config import Config

class RepoError(LocalRepoError):
	''' Handles repo errors '''
	pass

class DbError(RepoError):
	''' Handles database errors '''
	pass

class CacheError(RepoError):
	''' Handles cache errors '''
	pass

class Repo:
	''' A class handles a repository '''

	#: Database file extension
	EXT = '.db.tar.gz'

	#: Database link extension
	LINKEXT = '.db'

	#: Signature file extension
	SIGEXT = '.sig'

	#: Default cache filename
	CACHE = '.cache'

	#: Filename of the description file
	DESC = 'desc'

	def __init__(self, path):
		''' Creates a repo object and loads the package list '''
		self._db = self.find_db(path)
		self._path = dirname(self._db)
		self._packages = {}
		self._cache = Config.get('cache', Repo.CACHE)

		if not isabs(self._cache):
			self._cache = join(self._path, self._cache)

	@property
	def path(self):
		''' Return the path to the repo '''
		return self._path

	def __len__(self):
		''' Returns the number of packages '''
		return len(self._packages)

	def __iter__(self):
		''' Returns an iterator over all packages '''
		return self._packages.__iter__()

	def __contains__(self, name):
		''' Tests if a package is in the repo '''
		return name in self._packages

	def __getitem__(self, name):
		''' Returns a package '''
		return self._packages[name]

	def add(self, pkg, force=False):
		''' Adds a new package to the repo '''
		if pkg.name in self:
			if not force or self._packages[pkg.name] == pkg:
				raise RepoError(_('Package is already in the repo: {0}').format(pkg.name))

			self._packages[pkg.name].remove()

		pkg.move(self._path, force)
		self._packages[pkg.name] = pkg

		try:
			Pacman.repo_add(self._db, [pkg.path])
		except PacmanError as e:
			self.clear_cache()
			raise DbError(_('Could not add packages to the db: {0}').format(e.message))

		self.update_cache()

	def remove(self, names):
		''' Removes one or more packages from the repo '''
		if type(names) is not list:
			names = [names]

		for name in (n for n in names if n in self):
			 self[name].remove()
			 del(self._packages[name])

		try:
			Pacman.repo_remove(self._db, names)
		except PacmanError as e:
			self.clear_cache()
			raise DbError(_('Could not remove packages from the db: {0}').format(e.message))

		self.update_cache()

	def check(self):
		''' Runs an integrity check '''
		errors, paths = [], []

		for pkg in self._packages.values():
			paths.append(pkg.path)

			if not pkg.has_valid_sha256sum:
				errors.append(_('Package has no valid checksum: {0}').format(pkg.path))

			if pkg.is_signed and not isfile(pkg.sigfile):
				errors.append(_('Missing signature for package: {0}').format(pkg.name))

		try:
			for p in (join(self._path, f) for f in listdir(self._path) if f.endswith(Package.EXT)):
				if p not in paths:
					errors.append(_('Package is not listed in repo database: {0}').format(p))
		except OSError:
			errors.append(_('Could not list directory: {0}').format(self._path))

		return errors

	def find_db(self, path):
		''' Finds the repo database '''
		path = abspath(path)

		if path.endswith(Repo.EXT):
			return path

		if path.endswith(Repo.LINKEXT):
			return splitext(path)[0] + Repo.EXT

		if not isdir(path):
			raise DbError(_('Could not find database: {0}').format(path))

		try:
			return next(join(path, f) for f in listdir(path) if f.endswith(Repo.EXT))
		except OSError:
			raise DbError(_('Could not list directory: {0}').format(path))
		except StopIteration:
			return join(path, Config.get('reponame') + Repo.EXT)

	def load(self):
		''' Loads the packages dict '''
		try:
			self._packages = self.load_from_cache()
		except CacheError:
			self._packages = self.load_from_db()
			self.update_cache()

	def load_from_db(self):
		''' Loads the package list from a repo database file '''
		if not isfile(self._db):
			return {}

		try:
			db = open_tarfile(self._db)
		except:
			raise DbError(_('Could not open database: {0}').format(self._db))

		packages = {}

		for member in (m for m in db.getmembers() if m.isfile() and basename(m.name) == Repo.DESC):
			try:
				desc = db.extractfile(member).read().decode('utf8')
				info = DescParser(desc).parse()
			except ParserError as e:
				raise DbError(_('Invalid db entry: {0}: {1}').format(member.name, e.message))
			except:
				raise DbError(_('Could not read db entry: {0}').format(member.name))

			path = join(self._path, info['filename'])
			packages[info['name']] = Package(info['name'], info['version'], path, info)

		try:
			db.close()
		except:
			raise DbError(_('Could not close database: {0}').format(self._db))

		return packages

	def restore_db(self):
		''' Deletes the database and creates a new one by adding all packages '''
		try:
			pkgs = [join(self._path, f) for f in listdir(self._path) if f.endswith(Package.EXT)]
		except OSError:
			raise DbError(_('Could not list directory: {0}').format(self._path))

		self.clear_cache()

		try:
			if isfile(self._db):
				remove(self._db)
		except:
			raise DbError(_('Could not remove database: {0}').format(self._db))

		if pkgs:
			Pacman.repo_add(self._db, pkgs)

	def load_from_cache(self):
		''' Loads the package dict from a cache file '''
		try:
			ctime = getctime(self._cache)

			if getctime(self._db) > ctime or getctime(__file__) > ctime:
				raise CacheError(_('Cache is outdated: {0}').format(self._cache))
		except OSError:
			raise CacheError(_('Cache is outdated: {0}').format(self._cache))

		try:
			with open(self._cache, 'rb') as f:
				return unpickle(f)
		except:
			raise CacheError(_('Could not load cache: {0}').format(self._cache))

	def update_cache(self):
		''' Saves the package list in a cache file '''
		try:
			if not isdir(dirname(self._cache)):
				makedirs(dirname(self._cache), mode=0o755)

			with open(self._cache, 'wb') as f:
				pickle(self._packages, f)
		except:
			self.clear_cache()
			raise CacheError(_('Could not update cache: {0}').format(self._cache))

	def clear_cache(self):
		''' Removes the cache file '''
		try:
			if isfile(self._cache):
				remove(self._cache)
		except:
			raise CacheError(_('Could not clear cache: {0}').format(self._cache))

	def __str__(self):
		''' Returns a nice string with some repo info '''
		info = {'location': self._path,
		        'packages': len(self),
		        'pgpsig': isfile(self._db + Repo.SIGEXT)}

		try:
			info['last update'] = round(getctime(self._db))
		except:
			info['last update'] = '-'

		return Humanizer.info(info)
