#!/usr/bin/env python3.2

import sys
import os
import subprocess
import tempfile
import shutil
import re
import tarfile

class Repo:
	def __init__(self, name, path):
		self.name = name
		self.path = os.path.abspath(path)
		self.db = os.path.join(self.path, self.name + '.db.tar.gz')
		self.packages = self.load()
		self.tmpdir = None

	def load(self):
		if not os.path.exists(self.db) or not tarfile.is_tarfile(self.db):
			raise Exception('Repo does not exist: ' + self.name)
			return None

		packages = {}
		db = tarfile.open(self.db, 'r')

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

	def update(self, packages):
		updates = {}

		for pkg in self.packages:
			if pkg not in packages:
				continue

			if self.packages[pkg]['version'] < packages[pkg]['version']:
				updates[pkg] = packages[pkg]

		return updates

	def add(self, name, pkg):
		if self.tmpdir is None:
			self.tmpdir = tempfile.mkdtemp('-local-repo')

		os.chdir(self.tmpdir)
		archive = os.path.basename(pkg['url'])

		if subprocess.call(['wget', '-O', archive, pkg['url']]) is not 0:
			raise Exception('An error occured in wget')

		if subprocess.call(['tar', '-xzf', archive]) is not 0:
			raise Exception('An error occured in tar')

		os.chdir(os.path.join(self.tmpdir, name))

		if subprocess.call(['makepkg', '-sf']) is not 0:
			raise Exception('An error ocurred in makepkg')

		filename = None

		for f in os.listdir(os.getcwd()):
			if f[-11:] == '.pkg.tar.xz':
				filename = f
				break

		if filename is None:
			raise Exception('Could not find any package file')

		if not os.path.exists(os.path.join(self.path, filename)):
			shutil.move(filename, self.path)

		os.chdir(self.path)

		if subprocess.call(['repo-add', self.db, filename]) is not 0:
			raise Exception('An error occured in repo-add')

		if (name in self.packages and self.packages[name]['version'] != pkg['version'] and
		    os.path.isfile(self.packages[name]['filename'])):
			os.remove(self.packages[name]['filename'])

		return True

	def remove(self, name):
		if name not in self.packages:
			raise Exception('Package not found: ' + name)

		os.chdir(self.path)

		if subprocess.call(['repo-remove', self.db, name]) is not 0:
			raise Exception('An error ocurred in repo-remove')

		if os.path.isfile(self.packages[name]['filename']):
			os.remove(self.packages[name]['filename'])

	def clean(self):
		if self.tmpdir is not None:
			shutil.rmtree(self.tmpdir)
