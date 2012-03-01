#!/usr/bin/env python3.2
# vim:ts=4:sw=4:noexpandtab

from os import listdir, remove, stat
from os.path import abspath, basename, dirname, isdir, isfile, join, normpath, splitext

import tarfile
import re

from localrepo.pacman import Pacman
from localrepo.package import Package
from localrepo.msg import Msg

class Repo:
	''' A class handles a repository '''

	#: Database file extension
	EXT = '.db.tar.gz'

	#: Database link extension
	LINKEXT = '.db'

	def __init__(self, path):
		''' Creates a repo object and loads the package list '''
		self._db = self.find_db(path)
		self._path = dirname(self._db)
		self._packages = self.load()

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
		''' Loads the package list from a repo database file '''
		if not isfile(self._db):
			return {}

		if not tarfile.is_tarfile(self._db):
			raise Exception(_('File is no valid database: {0}').format(self._db))

		db = tarfile.open(self._db)
		packages = {}

		for member in (m for m in db.getmembers() if m.isfile() and m.name.endswith('desc')):
			desc = db.extractfile(member).read().decode('utf8')
			infos  = dict(((k.lower(), v) for k, v in re.findall('%([A-Z256]+)%\n([^\n]+)\n', desc)))

			if any(True for k in ['name', 'version', 'filename'] if k not in infos):
				raise Exception(_('Missing database entry: {0}').format(r))

			path = join(self._path, infos['filename'])
			packages[infos['name']] = Package(infos['name'], infos['version'], path, infos)

		db.close()
		return packages

	def package(self, name):
		''' Return a single package specified by name '''
		if not self.has_package(name):
			raise Exception(_('Package not found: {0}').format(name))

		return self._packages[name]

	def has_package(self, name):
		''' Checks if repo has a package specified by name '''
		return name in self._packages

	def find_packages(self, q):
		''' Searches the package list for packages '''
		return [pkg for pkg in self._packages if q in pkg]

	def upgrade(self, pkg):
		''' Replaces a package by a newer one '''
		old = self.package(pkg.name)

		if old.version > pkg.version:
			raise Exception(_('Repo package is newer: {0} > {1}').format(old.version, pkg.version))

		self.remove(old.name)
		self.add(pkg)

	def add(self, pkg):
		''' Adds a new package to the repo '''
		if self.has_package(pkg.name):
			raise Exception(_('Package is already in the repo: {0}').format(pkg.name))

		pkg.move(self._path)
		Pacman.repo_add(self._db, [pkg.path])
		self._packages[pkg.name] = pkg

	def remove(self, names):
		''' Removes one or more packages from the repo '''
		if type(names) is not list:
			names = [names]

		for name in names:
			 self.package(name).remove()
			 del(self._packages[name])

		Pacman.repo_remove(self._db, names)

	def restore_db(self):
		''' Deletes the database and creates a new one by adding all packages '''
		if isfile(self._db):
			remove(self._db)

		pkgs = [join(self._path, f) for f in listdir(self._path) if f.endswith(Package.EXT)]

		if pkgs:
			Pacman.repo_add(self._db, pkgs)
			self._packages = self.load()

	def check(self):
		''' Runs an integrity check '''
		errors = []
		paths = []

		for pkg in self._packages.values():
			paths.append(pkg.path)

			if not pkg.has_valid_sha256sum:
				errors.append(_('Package has no valid checksum: {0}').format(pkg.path))

		for f in (f for f in listdir(self._path) if f.endswith(Package.EXT)):
			path = join(self._path, f)

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
