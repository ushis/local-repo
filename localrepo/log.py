# log.py
# vim:ts=4:sw=4:noexpandtab

from os import makedirs, remove
from os.path import basename, dirname, isabs, isdir, isfile, join
from shutil import copytree, move, rmtree
from time import strftime

from localrepo.utils import LocalRepoError
from localrepo.config import Config

class LogError(LocalRepoError):
	''' Handles log errors '''
	pass


class BuildLogError(LogError):
	''' Handles build log errors '''
	pass


class PkgbuildLogError(LogError):
	''' Handles pkgbuild log errors '''
	pass


class Log:
	''' Handles Logging '''

	#: Default log filename
	FILENAME = '.log'

	#: Path to the log file
	_path = None

	#: Log file object
	_file = None

	@staticmethod
	def init(repo_path):
		''' Sets the path and opens the log file '''
		Log._path = Config.get('log', Log.FILENAME)

		if not isabs(Log._path):
			Log._path = join(repo_path, Log._path)

		try:
			if not isdir(dirname(Log._path)):
				makedirs(dirname(Log._path), mode=0o755, exist_ok=True)
			Log._file = open(Log._path, 'a')
		except:
			raise LogError(_('Could not open log file: {0}').format(Log._path))

	@staticmethod
	def log(msg):
		''' Logs a message '''
		try:
			Log._file.write('[{0}] {1}\n'.format(strftime('%Y-%m-%d %H:%M'), msg))
		except:
			pass

	@staticmethod
	def error(message):
		''' Logs an error '''
		Log.log(_('[Error] {0}').format(message))

	@staticmethod
	def close():
		''' Closes the log file '''
		try:
			Log._file.close()
		except:
			pass


class BuildLog:
	''' Stores build logs '''

	#: Default buildlog dirname
	DIRNAME = '.buildlog'

	#: Path to the buildlogs
	_path = None

	@staticmethod
	def init(repo_path):
		''' Sets the path '''
		BuildLog._path = Config.get('buildlog', BuildLog.DIRNAME)

		if not isabs(BuildLog._path):
			BuildLog._path = join(repo_path, BuildLog._path)

	@staticmethod
	def store(pkg_name, buildlog):
		''' Stores a buildlog '''
		path = join(BuildLog._path, pkg_name)

		try:
			if not isdir(path):
				makedirs(path, mode=0o755, exist_ok=True)

			move(buildlog, join(path, basename(buildlog)))
		except:
			raise BuildLogError(_('Could not store log file: {0} -> {1}').format(buildlog, path))


class PkgbuildLog:
	''' Stores PKGBUILDs '''

	#: Default dirname
	DIRNAME = '.pkgbuild'

	#: Path to the pkgbuilds
	_path = None

	@staticmethod
	def init(repo_path):
		''' Sets the path '''
		PkgbuildLog._path = Config.get('pkgbuild', PkgbuildLog.DIRNAME)

		if not isabs(PkgbuildLog._path):
			PkgbuildLog._path = join(repo_path, PkgbuildLog._path)

	@staticmethod
	def _copy(src, dst):
		''' Copies a PKGBUILD dir from src to  dst '''
		if src == dst:
			return

		try:
			if isfile(dst):
				remove(dst)
			elif isdir(dst):
				rmtree(dst)
			elif not isdir(dirname(dst)):
				makedirs(dirname(dst), mode=0o755)

			copytree(src, dst)
		except:
			raise PkgbuildLogError(_('Could not copy PKGBUILD dir: {0} -> {1}').format(src, dst))

	@staticmethod
	def log_dir(name):
		''' Returns the log directory for a package specified by name '''
		return join(PkgbuildLog._path, name)

	@staticmethod
	def store(name, path):
		''' Stores the whole PKGBUILD dir '''
		PkgbuildLog._copy(path, PkgbuildLog.log_dir(name))

	@staticmethod
	def load(name, path):
		''' Loads a stored pkgbuild dir into path '''
		PkgbuildLog._copy(PkgbuildLog.log_dir(name), path)
