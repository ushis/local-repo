# config.py
# vim:ts=4:sw=4:noexpandtab

from os import makedirs
from os.path import abspath, dirname, exists, expanduser, isdir, join
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
	TYPES = {'path': str,
	         'cache': str,
	         'log': str,
	         'buildlog': str,
	         'pkgbuild': str}

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
			return

		try:
			Config._parser.read_file(open(path))
		except:
			raise ConfigError(_('Could not parse config file: {0}').format(path))

		if not Config._parser.has_section(repo):
			Config._repo = Config.find_repo_by_path(repo)

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

		Config._parser.set(Config._repo, option, val)

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
			Config._parser.write(open(path, 'w'))
		except:
			raise ConfigError(_('Could not save config file: {0}').format(path))
