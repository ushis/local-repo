# pacman.py
# vim:ts=4:sw=4:noexpandtab

from os import chdir, getuid
from os.path import exists, isdir
from subprocess import call, check_output, CalledProcessError

class PacmanError(Exception):
	''' Handles programm call errors '''

	def __init__(self, cmd):
		''' Sets the failed command '''
		self._cmd = cmd

	def __str__(self):
		return _('An error occurred while running: {0}').format(self._cmd)

class Pacman:
	''' A wrapper for program calls of the pacman package '''

	#: Path to sudo
	SUDO = '/usr/bin/sudo'

	#: Path to su
	SU = '/bin/su'

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

	@staticmethod
	def call(cmd):
		''' Calls a command '''
		if type(cmd) is str:
			cmd = [cmd]

		if call(cmd) is not 0:
			raise PacmanError(' '.join(cmd))

	@staticmethod
	def install(pkgs, asdeps=False):
		''' Installs packages '''
		cmd = [Pacman.PACMAN, '-S'] + pkgs

		if asdeps:
			cmd.append('--asdeps')

		if getuid() is not 0:
			if exists(Pacman.SUDO):
				cmd.insert(0, Pacman.SUDO)
			else:
				cmd = [Pacman.SU, '-c', '\'{0}\''.format(' '.join(cmd))]

		Pacman.call(cmd)

	@staticmethod
	def install_as_deps(pkgs):
		''' Installs packages as dependencies '''
		Pacman.install(pkgs, True)

	@staticmethod
	def check_deps(pkgs):
		''' Checks for unresolved dependencies '''
		try:
			check_output([Pacman.PACMAN, '-T'] + pkgs)
			return []
		except CalledProcessError as e:
			if e.returncode is 127:
				return [p for p in e.output.decode('utf8').split('\n') if p]

			raise PacmanError(Pacman.PACMAN + ' -T')

	@staticmethod
	def make_package(path):
		''' Calls makepkg '''
		if not isdir(path):
			raise IOError(_('Could not find directory: {0}').format(path))

		chdir(path)
		Pacman.call([Pacman.MAKEPKG, '-d'])

	@staticmethod
	def repo_add(db, pkgs):
		''' Calls repo-add  '''
		Pacman.call([Pacman.REPO_ADD, db] + pkgs)

	@staticmethod
	def repo_remove(db, pkgs):
		''' Calls repo-remove '''
		Pacman.call([Pacman.REPO_REMOVE, db] + pkgs)

	@staticmethod
	def repo_elephant():
		''' The elephant never forgets '''
		if call([Pacman.REPO_ELEPHANT]) is not 0:
			raise Exception(_('Ooh no! Somebody killed the repo elephant'))
