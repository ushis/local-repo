#!/usr/bin/env python3.2

from localrepo.package import Package
from localrepo.repo import Repo
from localrepo.aur import Aur
from localrepo.msg import Msg

class LocalRepo:
	''' The main class for the local-repo programm '''

	def __init__(self, path):
		''' The constructor needs the path to the repo database file '''
		Msg.process('Loading repo database:', path)
		self.repo = Repo(path)

	def print_size(self):
		''' Prints the number of packages '''
		Msg.info(str(self.repo.size), 'packages found')

	def list_packages(self):
		''' Print all repo packages '''
		if self.repo.size is 0:
			Msg.info('This repo has no packages')
			return

		for name, pkg in sorted(self.repo.packages.items()):
			Msg.info(pkg.name, pkg.version)

	def package_info(self, name):
		''' Print all available info of apackage '''
		if not self.repo.has_package(name):
			Msg.error('Package does not exist:', name)
			return False

		for k, v in self.repo.package(name).infos.items():
			Msg.info('{0:10} {1}'.format(k, v))

		return True

	def find_packages(self, q):
		''' Search the repo for packages '''
		res = self.repo.find_packages(q)

		if not res:
			Msg.info('No package found')
			return

		for r in res:
			Msg.info(r, self.repo.package(r).version)

	def add_package(self, path, upgrade=False):
		''' Add a package to the repo '''
		Msg.process('Making a new package')

		try:
			pkg = Package.forge(path)

			if upgrade:
				Msg.process('Upgrading package:', pkg.name)
				self.repo.upgrade(pkg)
			else:
				Msg.process('Adding package to the repo:', pkg.name)
				self.repo.add(pkg)

			return True
		except Exception as e:
			Msg.error(str(e))
			return False

	def remove_package(self, name):
		''' Remove a package from the repo '''
		if not self.repo.has_package(name):
			Msg.error('Package does not exist:', name)
			return False

		Msg.process('Removing package:', name)

		try:
			self.repo.remove(name)
			return True
		except Exception as e:
			Msg.error(str(e))
			return False

	def add_package_from_aur(self, name):
		''' Download, make and add a package from the AUR '''
		Msg.process('Retrieving package infos from the AUR')

		try:
			pkg = Aur.package(name)
		except Exception as e:
			Msg.error(str(e))
			return False

		if self.repo.has_package(pkg['name']):
			Msg.error('Package is already in the repo:', pkg['name'])
			return False

		return self.add_package(pkg['uri'])

	def upgrade_aur_packages(self):
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

		for pkg in updates:
			if not self.add_package(pkg['uri'], True):
				return False

		return True

	def check(self):
		''' Run an integrity check '''
		Msg.info(str(self.repo.size), 'packages found')
		Msg.process('Running integrity check')
		errors = self.repo.check()

		if not errors:
			Msg.info('No errors found')

		for e in errors:
			Msg.error(e)

	def restore_db(self):
		''' Try to restore the database file '''
		Msg.process('Restoring database')

		try:
			self.repo.restore_db()
			return True
		except Exception as e:
			Msg.error(str(e))
			return False

	@staticmethod
	def shutdown(error):
		''' Clean up '''
		Package.clean()
		exit(0) if not error else exit(1)

	@staticmethod
	def abort():
		Msg.error('Execution cancelled by user')
		LocalRepo.shutdown(True)
