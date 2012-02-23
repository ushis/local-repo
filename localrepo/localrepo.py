#!/usr/bin/env python3.2

from localrepo.package import Package
from localrepo.repo import Repo
from localrepo.aur import Aur
from localrepo.msg import Msg

class LocalRepo:
	''' The main class for the local-repo programm '''

	@staticmethod
	def shutdown(error):
		''' Clean up '''
		Package.clean()
		exit(0) if not error else exit(1)

	@staticmethod
	def abort():
		Msg.error('Execution cancelled by user')
		LocalRepo.shutdown(True)

	def __init__(self, path):
		''' The constructor needs the path to the repo database file '''
		Msg.process('Loading repo database:', path)

		try:
			self.repo = Repo(path)
		except Exception as e:
			Msg.error(str(e))
			LocalRepo.shutdown(True)

	def size(self):
		''' Prints the number of packages '''
		Msg.info(str(self.repo))
		return True

	def list(self):
		''' Print all repo packages '''
		if self.repo.size is 0:
			Msg.info('This repo has no packages')
			return True

		for name, pkg in sorted(self.repo.packages.items()):
			Msg.info(pkg.name, pkg.version)

		return True

	def info(self, names):
		''' Print all available info of specified packages '''
		for name in names:
			if not self.repo.has_package(name):
				Msg.error('Package does not exist:', name)
				return False

			Msg.process('Package informations:', name)
			Msg.info(str(self.repo.package(name)))

		return True

	def find(self, q):
		''' Search the repo for packages '''
		res = self.repo.find_packages(q)

		if not res:
			Msg.info('No package found')
			return True

		for r in res:
			Msg.info(r, self.repo.package(r).version)

		return True

	def add(self, paths, upgrade=False):
		''' Add packages to the repo '''
		for path in paths:
			Msg.process('Making a new package')

			try:
				pkg = Package.forge(path)

				if upgrade:
					Msg.process('Upgrading package:', pkg.name)
					self.repo.upgrade(pkg)
				else:
					Msg.process('Adding package to the repo:', pkg.name)
					self.repo.add(pkg)
			except Exception as e:
				Msg.error(str(e))
				return False

		return True

	def upgrade(self, paths):
		''' Upgrade packages '''
		return self.add(paths, True)

	def remove(self, names):
		''' Remove packages from the repo '''
		for name in names:
			if not self.repo.has_package(name):
				Msg.error('Package does not exist:', name)
				return False

			Msg.process('Removing package:', name)

			try:
				self.repo.remove(name)
			except Exception as e:
				Msg.error(str(e))
				return False

		return True

	def aur_add(self, names):
		''' Download, make and add packages from the AUR '''
		Msg.process('Retrieving package infos from the AUR')

		try:
			pkgs = Aur.packages(names)
		except Exception as e:
			Msg.error(str(e))
			return False

		for pkg in pkgs.values():
			if self.repo.has_package(pkg['name']):
				Msg.error('Package is already in the repo:', pkg['name'])
				return False

			if not self.add([pkg['uri']]):
				return False

		return True

	def aur_upgrade(self):
		''' Upgrades all packages from the AUR '''
		Msg.info(str(self.repo.size), 'packages found')
		Msg.process('Retrieving package infos from the AUR')

		try:
			pkgs = Aur.packages(self.repo.packages)
		except Exception as e:
			Msg.error(str(e))
			return False

		Msg.info(str(len(pkgs)), 'packages found')
		Msg.process('Checking for updates')
		updates = []

		for name in (pkg for pkg in pkgs if self.repo.has_package(pkg)):
			if pkgs[name]['version'] > self.repo.package(name).version:
				updates.append(pkgs[name])

		if not updates:
			Msg.info('All packages are up to date')
			return True

		for pkg in updates:
			Msg.result('{0} ({1} -> {2})'.format(pkg['name'], self.repo.package(pkg['name']).version,
			                                     pkg['version']))

		if not Msg.yes('Upgrade'):
			Msg.info('Bye')
			return True

		return self.add([pkg['uri'] for pkg in updates], True)

	def check(self):
		''' Run an integrity check '''
		Msg.info(str(self.repo.size), 'packages found')
		Msg.process('Running integrity check')
		errors = self.repo.check()

		if not errors:
			Msg.info('No errors found')
			return True

		for e in errors:
			Msg.error(e)

		return True

	def restore(self):
		''' Try to restore the database file '''
		Msg.process('Restoring database')

		try:
			self.repo.restore_db()
			return True
		except Exception as e:
			Msg.error(str(e))
			return False

	def elephant(self):
		''' The elephant never forgets '''
		try:
			self.repo.elephant()
			return True
		except Exception as e:
			Msg.error(str(e))
			return False
