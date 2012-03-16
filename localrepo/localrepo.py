# localrepo.py
# vim:ts=4:sw=4:noexpandtab

from localrepo.package import Package, DependencyError
from localrepo.pacman import Pacman
from localrepo.repo import Repo
from localrepo.aur import Aur
from localrepo.msg import Msg

class LocalRepo:
	''' The main class for the local-repo programm '''

	@staticmethod
	def _install_deps(names):
		''' Installs missing dependencies '''
		Msg.info(_('Need following packages as dependencies: {0}').format(', '.join(names)))

		if not Msg.yes(_('Install')):
			if Msg.yes(_('Try without installing dependencies')):
				return True

			Msg.info(_('Bye'))
			return False

		try:
			Pacman.install_as_deps(names)
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
		Msg.error(_('Execution cancelled by user'))
		LocalRepo.shutdown(True)

	def __init__(self, path):
		''' The constructor needs the path to the repo database file '''
		try:
			self.repo = Repo(path)
		except Exception as e:
			Msg.error(str(e))
			LocalRepo.shutdown(True)

	def clear_cache(self):
		''' Clears the repo cache '''
		Msg.process(_('Clearing the cache'))

		try:
			self.repo.clear_cache()
			return True
		except Exception as e:
			Msg.error(str(e))
			return False

	def load(self):
		''' Loads the repo '''
		Msg.process(_('Loading repo database: {0}').format(self.repo.path))
		self.repo.load()

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
			if not self.repo.has(name):
				Msg.error(_('Package does not exist:'), name)
				return False

			Msg.process(_('Package information:'), name)
			Msg.info(str(self.repo.package(name)))

		return True

	def find(self, q):
		''' Search the repo for packages '''
		res = self.repo.find(q)

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
				if not LocalRepo._install_deps(e.deps):
					return False

				try:
					pkg = Package.from_pkgbuild(e.pkgbuild, True)
				except Exception as e:
					Msg.error(str(e))
					return False
			except Exception as e:
				Msg.error(str(e))
				return False

			try:
				if upgrade:
					Msg.process(_('Upgrading package:'), pkg.name)
					self.repo.add(pkg, force=True)
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
		bad = [name for name in names if not self.repo.has(name)]

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
			if self.repo.has(pkg['name']):
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

		for name in (pkg for pkg in pkgs if self.repo.has(pkg)):
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

		vcs = self.repo.vcs_packages

		if not vcs:
			Msg.info(_('No VCS packages found'))
			return True

		try:
			updates = Aur.packages(vcs)
		except Exception as e:
			Msg.error(str(e))
			return False

		Msg.result('\n'.join(updates))

		if not Msg.yes(_('Upgrade')):
			Msg.info(_('Bye'))
			return True

		return self.add([pkg['uri'] for pkg in updates.values()], True)

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
			Pacman.repo_elephant()
			return True
		except Exception as e:
			Msg.error(str(e))
			return False
