# localrepo.py
# vim:ts=4:sw=4:noexpandtab

from localrepo.package import Package, DependencyError
from localrepo.pacman import Pacman
from localrepo.repo import Repo
from localrepo.aur import Aur
from localrepo.log import Log, BuildLog, PkgbuildLog
from localrepo.utils import Msg, LocalRepoError
from localrepo.config import Config

class LocalRepo:
	''' The main class for the local-repo programm '''

	#: The repo instance
	_repo = None

	@staticmethod
	def shutdown(status=0):
		''' Cleans up and exits with status '''
		Package.clean()
		Log.close()
		exit(status)

	@staticmethod
	def error(error):
		''' Prints the error message and shuts down '''
		Msg.error(error.message)
		Log.error(error.message)
		LocalRepo.shutdown(1)

	@staticmethod
	def abort():
		''' This called by KeyboardInterrupt '''
		Msg.error(_('Execution cancelled by user'))
		LocalRepo.shutdown(1)

	@staticmethod
	def init(path, config_file=Config.CONFIGFILE):
		''' Needs the path to repo, or the repo name if specified in the config file '''
		try:
			Config.init(path, config_file)
			LocalRepo._repo = Repo(Config.get('path', path))
			Log.init(LocalRepo._repo.path)
			BuildLog.init(LocalRepo._repo.path)
			PkgbuildLog.init(LocalRepo._repo.path)
		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def load_repo():
		''' Loads the repo '''
		Msg.process(_('Loading repo: {0}').format(LocalRepo._repo.path))

		try:
			LocalRepo._repo.load()
		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def repo_info():
		''' Prints some repo info '''
		Msg.info(LocalRepo._repo)

	@staticmethod
	def list():
		''' Prints all repo packages '''
		if len(LocalRepo._repo) is 0:
			Msg.info(_('This repo has no packages'))
			return

		for name in sorted(LocalRepo._repo):
			Msg.info(name, LocalRepo._repo[name].version)

	@staticmethod
	def info(names):
		''' Prints all available info of specified packages '''
		for name in names:
			if name not in LocalRepo._repo:
				Msg.error(_('Package does not exist: {0}').format(name))
				LocalRepo.shutdown(1)

			Msg.process(_('Package information: {0}').format(name))
			Msg.info(LocalRepo._repo[name])

	@staticmethod
	def find(q):
		''' Searches the repo for packages '''
		res = sorted((name for name in LocalRepo._repo if q in name))

		if not res:
			Msg.error(_('No package found'))
			return

		for name in res:
			Msg.info(name, LocalRepo._repo[name].version)

	@staticmethod
	def _install_deps(names):
		''' Installs missing dependencies '''
		Msg.info(_('Need following packages as dependencies:\n[{0}]').format(', '.join(names)))

		if not Msg.ask(_('Install?')):
			if Msg.ask(_('Try without installing dependencies?')):
				return False

			Msg.info(_('Bye'))
			LocalRepo.shutdown(1)

		try:
			Pacman.install(names, as_deps=True)
			return True
		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def _uninstall_deps(names):
		''' Uninstalls previoulsy installed dependencies '''
		Msg.info(_('Installed following packages as dependencies:\n[{0}]').format(', '.join(names)))

		if Msg.ask(_('Uninstall?')):
			try:
				Pacman.uninstall(names)
			except LocalRepoError as e:
				LocalRepo.error(e)

	@staticmethod
	def _make_package(path, force=False):
		''' Makes a new package '''
		Msg.process(_('Forging a new package: {0}').format(path))
		Log.log(_('Forging a new package: {0}').format(path))

		try:
			return Package.forge(path, force=force)
		except DependencyError as e:
			installed_deps = LocalRepo._install_deps(e.deps)

			try:
				pkg = Package.from_pkgbuild(e.pkgbuild, ignore_deps=True, force=force)
			except LocalRepoError as e:
				LocalRepo.error(e)

			if Config.get('uninstall-deps', True) and installed_deps:
				LocalRepo._uninstall_deps(e.deps)

			return pkg

		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def add(paths, force=False):
		''' Adds packages to the repo '''
		for path in paths:
			pkg = LocalRepo._make_package(path, force=force)

			try:
				Msg.process(_('Adding package to the repo: {0}').format(pkg.name))
				LocalRepo._repo.add(pkg, force=force)
				Log.log(_('Added Package: {0} {1}').format(pkg.name, pkg.version))
			except LocalRepoError as e:
				LocalRepo.error(e)

	@staticmethod
	def rebuild(names):
		''' Rebuilds the specified packages '''
		if not Config.get('pkgbuild', False):
			LocalRepo.error(_('Please specify \'pkgbuild\' in your config file!'))

		LocalRepo.add([PkgbuildLog.log_dir(name) for name in names], force=True)

	@staticmethod
	def remove(names):
		''' Removes packages from the repo '''
		missing = [name for name in names if name not in LocalRepo._repo]

		if missing:
			Msg.error(_('Packages do not exist: {0}').format(', '.join(missing)))
			LocalRepo.shutdown(1)

		Msg.process(_('Removing packages: {0}').format(', '.join(names)))

		try:
			LocalRepo._repo.remove(names)
			Log.log(_('Removed packages: {0}').format(', '.join(names)))
		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def aur_add(names, force=False):
		''' Downloads, makes and adds packages from the AUR '''
		Msg.process(_('Retrieving package info from the AUR'))
		pkgs, errors = Aur.packages(names)

		for e in errors:
			Msg.error(e)

		for pkg in pkgs.values():
			if not force and pkg['name'] in LocalRepo._repo:
				Msg.error(_('Package is already in the repo: {0}').format(pkg['name']))
				LocalRepo.shutdown(1)

			LocalRepo.add([pkg['uri']], force=force)

	@staticmethod
	def aur_upgrade():
		''' Upgrades all packages from the AUR '''
		pkgs = [pkg for pkg in LocalRepo._repo if pkg not in Config.get('no-aur-upgrade', [])]
		Msg.info(_('{0} packages found').format(len(pkgs)))
		Log.log(_('Starting an AUR upgrade'))

		if len(pkgs) is 0:
			Msg.info(_('Nothing to do'))
			return

		Msg.process(_('Retrieving package info from the AUR'))
		pkgs, errors = Aur.packages(pkgs)

		for e in errors:
			Msg.error(e)

		Msg.info(_('{0} packages found').format(len(pkgs)))
		Msg.process(_('Checking for updates'))
		updates = []

		for name, pkg in ((name, pkg) for name, pkg in pkgs.items() if name in LocalRepo._repo):
			oldpkg = LocalRepo._repo[name]

			if oldpkg.has_smaller_version_than(pkg['version']):
				updates.append(pkg)
				Msg.result('{0} ({1} -> {2})'.format(name, oldpkg.version, pkg['version']))

		if not updates:
			Msg.info(_('All packages are up to date'))
			return

		if not Msg.ask(_('Upgrade?')):
			Msg.info(_('Bye'))
			LocalRepo.shutdown(1)

		LocalRepo.add([pkg['uri'] for pkg in updates], force=True)

	@staticmethod
	def vcs_upgrade():
		''' Upgrades all VCS packages from the AUR '''
		Msg.process(_('Updating all VCS packages'))
		Log.log(_('Starting a VCS upgrade'))
		vcs = [pkg for pkg in LocalRepo._repo if LocalRepo._repo[pkg].is_vcs]

		if not vcs:
			Msg.info(_('No VCS packages found'))
			return

		Msg.process(_('Retrieving package info from the AUR'))
		updates, errors = Aur.packages(vcs)

		for e in errors:
			Msg.error(e)

		if not updates:
			Msg.info(_('No updates found'))
			return

		Msg.result('\n'.join(updates))

		if not Msg.ask(_('Upgrade?')):
			Msg.info(_('Bye'))
			return

		LocalRepo.add([pkg['uri'] for pkg in updates.values()], force=True)

	@staticmethod
	def clear_cache():
		''' Clears the repo cache '''
		Msg.process(_('Clearing the cache'))

		try:
			LocalRepo._repo.clear_cache()
			Log.log(_('Cleared cache'))
		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def check():
		''' Run an integrity check '''
		Msg.info(_('{0} packages found').format(len(LocalRepo._repo)))
		Msg.process(_('Running integrity check'))
		errors = LocalRepo._repo.check()

		if not errors:
			Msg.info(_('No errors found'))
			Log.log(_('Finished integrity check without any errors'))
			return

		Log.log(_('Finished integrity check with errors:'))

		for e in errors:
			Msg.result(e)
			Log.error(e)

	@staticmethod
	def restore_db():
		''' Try to restore the database file '''
		Msg.process(_('Restoring database'))

		try:
			LocalRepo._repo.restore_db()
			Log.log(_('Restored Database'))
		except LocalRepoError as e:
			LocalRepo.error(e)

	@staticmethod
	def elephant():
		''' The elephant never forgets '''
		try:
			Pacman.repo_elephant()
		except LocalRepoError as e:
			LocalRepo.error(e)
