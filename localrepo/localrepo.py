# localrepo.py
# vim:ts=4:sw=4:noexpandtab

import re

from localrepo.package import Package, DependencyError
from localrepo.pacman import Pacman
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
		Msg.error(_('Execution cancelled by user'))
		LocalRepo.shutdown(True)

	def __init__(self, path):
		''' The constructor needs the path to the repo database file '''
		Msg.process(_('Loading repo database:'), path)

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
			Msg.info(_('This repo has no packages'))
			return True

		for name, pkg in sorted(self.repo.packages.items()):
			Msg.info(pkg.name, pkg.version)

		return True

	def info(self, names):
		''' Print all available info of specified packages '''
		for name in names:
			if not self.repo.has_package(name):
				Msg.error(_('Package does not exist:'), name)
				return False

			Msg.process(_('Package information:'), name)
			Msg.info(str(self.repo.package(name)))

		return True

	def find(self, q):
		''' Search the repo for packages '''
		res = self.repo.find_packages(q)

		if not res:
			Msg.error(_('No package found'))
			return True

		for r in res:
			Msg.info(r, self.repo.package(r).version)

		return True

	def add(self, paths, upgrade=False):
		''' Add packages to the repo '''
		for path in paths:
			Msg.process(_('Making a new package'))

			try:
				pkg = Package.forge(path)
			except DependencyError as e:
				Msg.info(_('Need following packages as makedepends: {0}').format(', '.join(e.deps)))

				if not Msg.yes(_('Install')):
					return False

				try:
					Pacman.install_as_deps(e.deps)
					pkg = Package.forge(e.pkgbuild)
				except Exception as e:
					Msg.error(str(e))
					return False
			except Exception as e:
				Msg.error(str(e))
				return False

			try:

				if upgrade:
					Msg.process(_('Upgrading package:'), pkg.name)
					self.repo.upgrade(pkg)
				else:
					Msg.process(_('Adding package to the repo:'), pkg.name)
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
		bad = [name for name in names if not self.repo.has_package(name)]

		if bad:
			Msg.error(_('Packages do not exist:'), ', '.join(bad))
			return False

		Msg.process(_('Removing packages:'), ', '.join(names))

		try:
			self.repo.remove(names)
			return True
		except Exception as e:
			Msg.error(str(e))
			return False

	def aur_add(self, names):
		''' Download, make and add packages from the AUR '''
		Msg.process(_('Retrieving package info from the AUR'))

		try:
			pkgs = Aur.packages(names)
		except Exception as e:
			Msg.error(str(e))
			return False

		for pkg in pkgs.values():
			if self.repo.has_package(pkg['name']):
				Msg.error(_('Package is already in the repo:'), pkg['name'])
				return False

			if not self.add([pkg['uri']]):
				return False

		return True

	def aur_upgrade(self):
		''' Upgrades all packages from the AUR '''
		Msg.info(_('{0} packages found').format(self.repo.size))

		if self.repo.size is 0:
			Msg.info(_('Nothing to do'))
			return True

		Msg.process(_('Retrieving package info from the AUR'))

		try:
			pkgs = Aur.packages(self.repo.packages)
		except Exception as e:
			Msg.error(str(e))
			return False

		Msg.info(_('{0} packages found').format(len(pkgs)))
		Msg.process(_('Checking for updates'))
		updates = []

		for name in (pkg for pkg in pkgs if self.repo.has_package(pkg)):
			if pkgs[name]['version'] > self.repo.package(name).version:
				updates.append(pkgs[name])

		if not updates:
			Msg.info(_('All packages are up to date'))
			return True

		for pkg in updates:
			Msg.result('{0} ({1} -> {2})'.format(pkg['name'],
			                                     self.repo.package(pkg['name']).version,
			                                     pkg['version']))

		if not Msg.yes(_('Upgrade')):
			Msg.info(_('Bye'))
			return True

		return self.add([pkg['uri'] for pkg in updates], True)

	def vcs_upgrade(self):
		''' Upgrades all VCS packages from the AUR '''
		Msg.process(_('Updating all VCS packages'))

		try:
			pkgs = Aur.packages(self.repo.packages)
		except Exception as e:
			Msg.error(str(e))
			return False

		vcs_pkgs = []
		for name in (pkg for pkg in pkgs if self.repo.has_package(pkg)):
			if re.search(r'-(cvs|svn|hg|darcs|bzr|git)$', pkgs[name]['name']):
				vcs_pkgs.append(pkgs[name])

		if not vcs_pkgs:
			Msg.info(_('No VCS packages found'))
			return True

		for pkg in vcs_pkgs:
			Msg.result('{0}'.format(pkg['name']))

		if not Msg.yes(_('Upgrade')):
			Msg.info(_('Bye'))
			return True

		return self.add([pkg['uri'] for pkg in vcs_pkgs], True)

	def check(self):
		''' Run an integrity check '''
		Msg.info(_('{0} packages found').format(self.repo.size))
		Msg.process(_('Running integrity check'))
		errors = self.repo.check()

		if not errors:
			Msg.info(_('No errors found'))
			return True

		for e in errors:
			Msg.error(e)

		return True

	def restore(self):
		''' Try to restore the database file '''
		Msg.process(_('Restoring database'))

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
