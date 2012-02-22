#!/usr/bin/env python3.2

from os.path import abspath, basename, isfile, isdir, join
from subprocess import call
from hashlib import sha256
from urllib.request import urlretrieve

import sys
import os
import shutil
import tempfile
import tarfile
import re
import math

class Package:
	''' The package class provides static methods for building packages and
	an objectiv part to manage existing packages '''

	#: Package file extenion
	EXT = '.pkg.tar.xz'

	#: Path to a temporary directory
	tmpdir = None

	@staticmethod
	def get_tmpdir():
		''' Creates a temporary directory '''
		if Package.tmpdir is None:
			Package.tmpdir = tempfile.mkdtemp('-local-repo')
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
		tmpdir = Package.get_tmpdir()
		path = join(tmpdir, basename(url))

		try:
			urlretrieve(url, path)
		except:
			raise Exception('Could not download file: {0}'.format(url))

		return Package.from_tarball(path)

	@staticmethod
	def from_tarball(path):
		''' Builds a package from a tarball '''
		tmpdir = Package.get_tmpdir()
		path = abspath(path)

		if not isfile(path) or not tarfile.is_tarfile(path):
			raise Exception('File is no valid tarball: {0}'.format(path))

		os.chdir(tmpdir)
		archive = tarfile.open(path)
		name = None

		for member in archive.getnames():
			if member.startswith('/') or member.startswith('..'):
				raise Exception('Tarball contains bad member: {0}'.format(member))

			root = member.split(os.sep)[0]

			if name is None:
				name = root
				continue

			if name != root:
				raise Exception('Tarball contains multiple root directories')

		archive.extractall()
		os.chdir(join(tmpdir, name))

		if call(['makepkg', '-s']) is not 0:
			raise Exception('An error ocurred in makepkg')

		filenames = [f for f in os.listdir() if f.endswith(Package.EXT)]

		if not filenames:
			raise Exception('Could not find any package')

		return Package.from_file(join(os.getcwd(), filenames[0]))

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
			raise Exception('File does not exist: {0}'.join(path))

		tmpdir = Package.get_tmpdir()

		if call(['tar', '-xJf', path, '-C', tmpdir, '.PKGINFO']) is not 0:
			raise Exception('An error occurred in tar')

		pkginfo = open(join(tmpdir, '.PKGINFO')).read()
		# End workaround

		infos = {}

		for i in re.findall('([a-z]+) = ([^\n]+)\n', pkginfo):
			infos[i[0]] = i[1]

		if any(True for r in ['pkgname', 'pkgver'] if r not in infos):
			raise Exception('Invalid .PKGINFO')

		return Package(infos['pkgname'], infos['pkgver'], path, infos)

	@staticmethod
	def forge(path):
		''' Forwards the path to an package builder '''
		if path.startswith('http://') or path.startswith('ftp://'):
			return Package.from_remote_tarball(path)

		if path.endswith('.tar.gz'):
			return Package.from_tarball(path)

		if path.endswith(Package.EXT):
			return Package.from_file(path)

		raise Exception('Invalid file name: {0}'.format(path))

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

	def move(self, path):
		''' Moves the package to a new location '''
		path = abspath(path)

		if not isdir(path):
			raise Exception('Destination is no directory: {0}'.format(path))

		path = join(path, self._filename)

		if isfile(path):
			raise Exception('File already exists: {0}'.format(path))

		shutil.move(self._path, path)
		self._path = path

	def remove(self):
		''' Removes the package file '''
		if not isfile(self._path):
			raise Exception('Package does not exist: {0}'.format(self._path))

		os.remove(self._path)
