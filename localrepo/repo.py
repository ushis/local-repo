#!/usr/bin/env python3.2

from os.path import abspath, dirname, isfile, join
from subprocess import call

import tarfile
import re

from localrepo.package import Package

class Repo:
	def __init__(self, path):
		self._db = abspath(path)
		self._path = dirname(self._db)
		self._packages = self.load()

	@property
	def packages(self):
		return self._packages

	@property
	def size(self):
		return len(self._packages)

	def load(self):
		if not isfile(self._db) or not tarfile.is_tarfile(self._db):
			raise Exception('No repo database found: {0}'.format(self._db))

		db = tarfile.open(self._db)
		packages = {}

		for member in db.getmembers():
			if not member.isfile() or not member.name.endswith('desc'):
				continue

			desc = db.extractfile(member).read().decode('utf8')
			infos = {}

			for i in re.findall('%([A-Z256]+)%\n([^\n]+)\n', desc):
				infos[i[0].lower()] = i[1]

			req = {'name': None, 'version': None, 'filename': None}

			for r in req:
				if r not in infos:
					raise Exception('Missing database entry: {0}'.format(r))

				req[r] = infos[r]
				del(infos[r])

			path = join(self._path, req['filename'])
			packages[req['name']] = Package(req['name'], req['version'], path, infos)

		return packages

	def package(self, name):
		if not self.has_package(name):
			raise Exception('Package not found: {0}'.format(name))

		return self._packages[name]

	def has_package(self, name):
		if name in self._packages:
			return True

		return False

	def find_packages(self, q):
		hits = []

		for pkg in self.packages:
			if q in pkg:
				hits.append(pkg)

		return hits

	def upgrade(self, pkg):
		old = self.package(pkg.name)

		if old.version > pkg.version:
			raise Exception('Repo package is newer: {0} > {1}'.format(old.version, new.version))

		self.remove(old.name)
		self.add(pkg)

	def add(self, pkg):
		if self.has_package(pkg.name):
			raise Exception('Package is already in the repo: {0}'.format(pkg.name))

		pkg.move(self._path)

		if call(['repo-add', self._db, pkg.path]) is not 0:
			raise Exception('An error occurred in repo-add')

		self.packages[pkg.name] = pkg

	def remove(self, name):
		pkg = self.package(name)

		if call(['repo-remove', self._db, pkg.name]) is not 0:
			raise Exception('An error occurred in repo-remove')

		del(self._packages[pkg.name])
		pkg.remove()

	def check(self):
		errors = []

		for name in self._packages:
			if not self._packages[name].has_valid_sha256sum:
				errors.append('Packge has no valid checksum: {0}'.format(self._packages[name].path))

		return errors
