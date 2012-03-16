# repo.py
# vim:ts=4:sw=4:noexpandtab

from os import listdir, remove, stat
from os.path import abspath, basename, dirname, isdir, isfile, join, normpath, splitext

import tarfile
import pickle
import re

from localrepo.pacman import Pacman
from localrepo.package import Package
from localrepo.parser import DescParser
from localrepo.msg import Msg

class Repo:
	''' A class handles a repository '''

	#: Database file extension
	EXT = '.db.tar.gz'

	#: Database link extension
	LINKEXT = '.db'

	#: Cache filename
	CACHE = '.cache'

	def __init__(self, path):
		''' Creates a repo object and loads the package list '''
		self._db = self.find_db(path)
		self._path = dirname(self._db)
		self._cache = join(self._path, Repo.CACHE)
		self._packages = {}

	@property
	def path(self):
		''' Return the path to the repo '''
		return self._path

	@property
	def packages(self):
		''' Returns the packages dict '''
		return self._packages

	@property
	def vcs_packages(self):
		''' Returns a list vcs packages '''
		regex = '^.+-(?:cvs|svn|hg|darcs|bzr|git)$'
		return [pkg for pkg in self._packages if re.match(regex, pkg)]

	@property
	def size(self):
		''' Returns the number of packages '''
		return len(self._packages)

	def find_db(self, path):
		''' Finds the repo database '''
		path = abspath(normpath(path))

		if path.endswith(Repo.LINKEXT):
			return splitext(path)[0] + Repo.EXT

		if path.endswith(Repo.EXT):
			return path

		if not isdir(path):
			raise Exception(_('Could not find repo database: {0}').format(path))

		for f in listdir(path):
			if f.endswith(Repo.EXT):
				return join(path, f)

		return join(path, basename(path).lower() + Repo.EXT)

	def load(self):
		''' Loads the packages dict '''
		try:
			self._packages = self.load_from_cache()
		except:
			self._packages = self.load_from_db()
			self.update_cache()

	def load_from_db(self):
		''' Loads the package list from a repo database file '''
		if not isfile(self._db):
			return {}

		if not tarfile.is_tarfile(self._db):
			raise Exception(_('File is no valid database: {0}').format(self._db))

		db = tarfile.open(self._db)
		packages = {}

		for member in (m for m in db.getmembers() if m.isfile() and m.name.endswith('desc')):
			desc = db.extractfile(member).read().decode('utf8')
			info = DescParser(desc).parse()
			path = join(self._path, info['filename'])
			packages[info['name']] = Package(info['name'], info['version'], path, info)

		db.close()
		return packages

	def load_from_cache(self):
		''' Loads the package dict from a cache file '''
		if not isfile(self._cache):
			raise IOError(_('File does not exist: {0}').format(self._cache))

		if stat(self._db).st_mtime > stat(self._cache).st_mtime:
			self.clear_cache()
			raise Exception(_('Cache is outdated'))

		try:
			return pickle.load(open(self._cache, 'rb'))
		except:
			self.clear_cache()
			raise Exception(_('Could not load cache'))

	def update_cache(self):
		''' Saves the package list in a cache file '''
		try:
			pickle.dump(self._packages, open(self._cache, 'wb'))
		except:
			self.clear_cache()
			raise Exception(_('Could not update cache'))

	def clear_cache(self):
		''' Removes the cache file '''
		if isfile(self._cache):
			remove(self._cache)

	def package(self, name):
		''' Return a single package specified by name '''
		if not self.has(name):
			raise Exception(_('Package not found: {0}').format(name))

		return self._packages[name]

	def has(self, name):
		''' Checks if repo has a package specified by name '''
		return name in self._packages

	def find(self, q):
		''' Searches the package list for packages '''
		return [pkg for pkg in self._packages if q in pkg]

	def add(self, pkg, force=False):
		''' Adds a new package to the repo '''
		if self.has(pkg.name):
			if not force:
				raise Exception(_('Package is already in the repo: {0}').format(pkg.name))

			self._packages[pkg.name].remove()

		pkg.move(self._path, force)
		self._packages[pkg.name] = pkg

		try:
			Pacman.repo_add(self._db, [pkg.path])
		except Exception as e:
			self.clear_cache()
			raise e

		self.update_cache()

	def remove(self, names):
		''' Removes one or more packages from the repo '''
		if type(names) is not list:
			names = [names]

		for name in names:
			 self.package(name).remove()
			 del(self._packages[name])

		try:
			Pacman.repo_remove(self._db, names)
		except Exception as e:
			self.clear_cache()
			raise e

		self.update_cache()

	def restore_db(self):
		''' Deletes the database and creates a new one by adding all packages '''
		if isfile(self._db):
			remove(self._db)

		pkgs = [join(self._path, f) for f in listdir(self._path) if f.endswith(Package.EXT)]

		if pkgs:
			Pacman.repo_add(self._db, pkgs)

		self.clear_cache()

	def check(self):
		''' Runs an integrity check '''
		errors, paths = [], []

		for pkg in self._packages.values():
			paths.append(pkg.path)

			if not pkg.has_valid_sha256sum:
				errors.append(_('Package has no valid checksum: {0}').format(pkg.path))

		for path in (join(self._path, f) for f in listdir(self._path) if f.endswith(Package.EXT)):
			if path not in paths:
				errors.append(_('Package is not listed in repo database: {0}').format(path))

		return errors

	def __str__(self):
		''' Return a nice string with some repo infos '''
		infos = {'location': self._path,
		         'packages': self.size}

		if isfile(self._db):
			infos['last update'] = round(stat(self._db).st_mtime)

		return Msg.human_infos(infos)
