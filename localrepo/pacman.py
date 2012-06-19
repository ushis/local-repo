# pacman.py
# vim:ts=4:sw=4:noexpandtab

from os import access, chdir, getuid, X_OK
from re import compile as compile_pattern
from subprocess import call, check_output, CalledProcessError

from localrepo.utils import LocalRepoError
from localrepo.config import Config

class PacmanError(LocalRepoError):
	''' Handles pacman errors '''
	pass


class PacmanCallError(PacmanError):
	''' Handles call errors '''

	def __init__(self, cmd):
		''' Sets the error message '''
		super().__init__(_('An error occurred while running: {0}').format(cmd))


class Pacman:
	''' A wrapper for program calls of the pacman package '''

	#: Path to su
	SU = '/bin/su'

	#: Path to sudo
	SUDO = '/usr/bin/sudo'

	#: Path to pacman
	PACMAN = '/usr/bin/pacman'

	#: Path to makepkg
	MAKEPKG = '/usr/bin/makepkg'

	#: Path to repo-add
	REPO_ADD = '/usr/bin/repo-add'

	#: Path to repo-remove
	REPO_REMOVE = '/usr/bin/repo-remove'

	#: Path to repo-elephant
	REPO_ELEPHANT = '/usr/bin/repo-elephant'

	#: Split pattern, used to remove the version requirement from the package name
	VERSION_SEP = compile_pattern('<|>|=')

	@staticmethod
	def call(cmd):
		''' Calls a command '''
		if type(cmd) is str:
			cmd = [cmd]

		if call(cmd) is not 0:
			raise PacmanCallError(' '.join(cmd))

	@staticmethod
	def _run_as_root(cmd):
		''' Runs a command as root '''
		if getuid() is not 0:
			if access(Pacman.SUDO, X_OK):
				cmd.insert(0, Pacman.SUDO)
			else:
				cmd = [Pacman.SU, '-c', '\'{0}\''.format(' '.join(cmd))]

		Pacman.call(cmd)

	@staticmethod
	def install(pkgs, as_deps=False):
		''' Installs packages '''
		cmd = [Pacman.PACMAN, '-Sy'] + pkgs

		if as_deps:
			cmd.append('--asdeps')

		Pacman._run_as_root(cmd)

	@staticmethod
	def uninstall(pkgs):
		''' Unnstalls packages '''
		for i, pkg in enumerate(pkgs):
			pkgs[i] = Pacman.VERSION_SEP.split(pkg)[0]

		Pacman._run_as_root([Pacman.PACMAN, '-Rs'] + list(set(pkgs)))

	@staticmethod
	def check_deps(pkgs):
		''' Checks for unresolved dependencies '''
		cmd = [Pacman.PACMAN, '-T'] + pkgs

		try:
			check_output(cmd)
			return []
		except CalledProcessError as e:
			if e.returncode is 127:
				return e.output.decode('utf8').split()

			raise PacmanCallError(' '.join(cmd))

	@staticmethod
	def make_package(path, force=False):
		''' Calls makepkg '''
		try:
			chdir(path)
		except:
			raise PacmanError(_('Could not change working directory: {0}').format(path))

		cmd = [Pacman.MAKEPKG, '-d']

		if force:
			cmd.append('-f')

		if Config.get('buildlog', False):
			cmd += ['-L', '-m']

		if Config.get('sign', False):
			cmd.append('--sign')
		else:
			cmd.append('--nosign')

		Pacman.call(cmd)

	@staticmethod
	def _repo_script(script, db, pkgs):
		''' Calls one of the repo- scripts '''
		cmd = [script, db] + pkgs

		if Config.get('signdb', False):
			cmd += ['--verify', '--sign']

		Pacman.call(cmd)

	@staticmethod
	def repo_add(db, pkgs):
		''' Calls repo-add  '''
		Pacman._repo_script(Pacman.REPO_ADD, db, pkgs)

	@staticmethod
	def repo_remove(db, pkgs):
		''' Calls repo-remove '''
		Pacman._repo_script(Pacman.REPO_REMOVE, db, pkgs)

	@staticmethod
	def repo_elephant():
		''' The elephant never forgets '''
		if call([Pacman.REPO_ELEPHANT]) is not 0:
			raise PacmanError(_('Ooh no! Somebody killed the repo elephant'))
