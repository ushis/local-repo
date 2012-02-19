#!/usr/bin/env python3.2

import sys
import os
import subprocess
import tempfile
import shutil
import re
import tarfile

class Repo:
	def __init__(self, path):
		self._db = os.path.abspath(path)
		self._path = os.path.dirname(self._db)
		self._tmpdir = None
		self._packages = self.load()

	@property
	def packages(self):
		return self._packages

	def load(self):
		if not os.path.isfile(self._db) or not tarfile.is_tarfile(self._db):
			raise Exception('Repo db does not exist: ' + self._db)

		packages = {}
		db = tarfile.open(self._db, 'r')

		for member in db.getmembers():
			if not member.isfile() or member.name[-4:] != 'desc':
				continue

			desc = db.extractfile(member).read().decode('utf8')
			infos = re.findall('%([A-Z]+)%\n([^\n]+)\n', desc)
			pkg = {}

			for i in infos:
				pkg[i[0].lower()] = i[1]

			if 'name' in pkg:
				packages[pkg['name']] = pkg

		return packages

	def size(self):
		return len(self._packages)

	def has_package(self, name):
		if name in self._packages:
			return True
		return False

	def package(self, name):
		if not self.has_package(name):
			raise Exception('Package not found: ' + name)
		return self._packages[name]

	def find_packages(self, q):
		found = []

		for pkg in self._packages:
			if q in pkg:
				found.append(pkg)

		return found

	def update(self, packages):
		updates = {}

		for pkg in self._packages:
			if pkg not in packages:
				continue

			if self._packages[pkg]['version'] < packages[pkg]['version']:
				updates[pkg] = packages[pkg]

		return updates

	def add(self, name, pkg):
		if self._tmpdir is None:
			self._tmpdir = tempfile.mkdtemp('-local-repo')

		os.chdir(self._tmpdir)
		archive = os.path.basename(pkg['url'])

		if subprocess.call(['wget', '-O', archive, pkg['url']]) is not 0:
			raise Exception('An error occured in wget')

		if subprocess.call(['tar', '-xzf', archive]) is not 0:
			raise Exception('An error occured in tar')

		os.chdir(os.path.join(self._tmpdir, name))

		if subprocess.call(['makepkg', '-sf']) is not 0:
			raise Exception('An error ocurred in makepkg')

		filename = None

		for f in os.listdir(os.getcwd()):
			if f[-11:] == '.pkg.tar.xz':
				filename = f
				break

		if filename is None:
			raise Exception('Could not find any package file')

		if not os.path.exists(os.path.join(self._path, filename)):
			shutil.move(filename, self._path)

		os.chdir(self._path)

		if subprocess.call(['repo-add', self._db, filename]) is not 0:
			raise Exception('An error occured in repo-add')

		if (name in self._packages and self._packages[name]['version'] != pkg['version'] and
		    os.path.isfile(self._packages[name]['filename'])):
			os.remove(self._packages[name]['filename'])

		return True

	def remove(self, name):
		if name not in self._packages:
			raise Exception('Package not found: ' + name)

		os.chdir(self._path)

		if subprocess.call(['repo-remove', self._db, name]) is not 0:
			raise Exception('An error ocurred in repo-remove')

		if os.path.isfile(self._packages[name]['filename']):
			os.remove(self._packages[name]['filename'])

	def __del__(self):
		if self._tmpdir is not None:
			shutil.rmtree(self._tmpdir)
