# config.py
# vim:ts=4:sw=4:noexpandtab

from os import makedirs
from os.path import abspath, basename, dirname, exists, expanduser, isdir, join
from configparser import ConfigParser

from localrepo.utils import LocalRepoError

class ConfigError(LocalRepoError):
	''' The config error class '''
	pass


class Config:
	''' A wrapper for the ConfigParser class '''

	#: Path to the config file
	CONFIGFILE = expanduser(join('~', '.config', 'local-repo'))

	#: Name of the global section
	ALL = 'all'

	#: Data types
	TYPES = {'buildlog': str,
	         'cache': str,
	         'log': str,
	         'no-aur-upgrade': list,
	         'path': str,
	         'pkgbuild': str,
	         'reponame': str,
	         'sign': bool,
	         'signdb': bool,
	         'uninstall-deps': bool}

	#: The ConfigParser instance
	_parser = ConfigParser()

	#: The used repo
	_repo = None

	@staticmethod
	def init(repo, path=CONFIGFILE):
		''' Sets the repo and loads the config file '''
		Config._repo = repo
		path = abspath(path)

		if not exists(path):
			Config.set_reponame()
			return

		try:
			f = open(path)
		except:
			raise ConfigError(_('Could not open config file: {0}').format(path))

		try:
			Config._parser.read_file(f)
		except:
			raise ConfigError(_('Could not parse config file: {0}').format(path))
		finally:
			f.close()

		if not Config._parser.has_section(repo):
			Config._repo = Config.find_repo_by_path(repo)

		Config.set_reponame()

	@staticmethod
	def set_reponame():
		Config.set('reponame', basename(Config._repo).lower())

	@staticmethod
	def normalize_path(path):
		''' Normalizes a repo path to make it compareable.
		E.g. /path/to/repo equals /path/to/repo/mydb.db.tar.gz '''
		path = abspath(path)
		return path if isdir(path) else dirname(path)

	@staticmethod
	def find_repo_by_path(path):
		''' Finds the repo name by path '''
		path = Config.normalize_path(path)

		for repo in (s for s in Config._parser.sections() if Config._parser.has_option(s, 'path')):
			if Config.normalize_path(Config._parser.get(repo, 'path')) == path:
				return repo

		return path

	@staticmethod
	def _get(section, option):
		''' Returns an option in the correct datatype '''
		datatype = Config.TYPES.get(option, str)

		if datatype is bool:
			return Config._parser.getboolean(section, option)

		if datatype is int:
			return Config._parser.getint(section, option)

		if datatype is float:
			return Config._parser.getfloat(section, option)

		if datatype is list:
			return Config._parser.get(section, option).split()

		return Config._parser.get(section, option)

	@staticmethod
	def get(option, default=None):
		''' Returns an option '''
		try:
			return Config._get(Config._repo, option)
		except:
			pass

		try:
			return Config._get(Config.ALL, option)
		except:
			return default

	@staticmethod
	def set(option, val):
		''' Sets an option '''
		if not Config._parser.has_section(Config._repo):
			Config._parser.add_section(Config._repo)

		if type(val) is bool:
			Config._parser.set(Config._repo, option, 'yes' if val else 'no')
		elif type(val) in (list, tuple):
			Config._parser.set(Config._repo, option, ' '.join((str(v) for v in val)))
		else:
			Config._parser.set(Config._repo, option, str(val))

	@staticmethod
	def remove(option):
		''' Removes an option '''
		Config._parser.remove_option(Config._repo, option)

	@staticmethod
	def save(path=CONFIGFILE):
		''' Saves options to config file '''
		try:
			if not isdir(dirname(path)):
				makedirs(dirname(path), mode=0o755, exist_ok=True)

			with open(path, 'w') as f:
				Config._parser.write(f)
		except:
			raise ConfigError(_('Could not save config file: {0}').format(path))
