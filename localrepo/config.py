# config.py
# vim:ts=4:sw=4:noexpandtab

from os.path import abspath, exists, expanduser, join
from configparser import ConfigParser

class ConfigError(Exception):
	''' The config error class '''

	def __init__(self, msg):
		''' Sets the error message '''
		self._msg = msg

	def message(self):
		''' Returns the error message '''
		return self._msg

	def __str__(self):
		''' Returns the error message '''
		return self._msg


class Config:
	''' A wrapper for the ConfigParser class '''

	#: Path to the config dir
	CONFIGDIR = expanduser(join('~', '.config'))

	#: Config filename
	CONFIGFILE = join(CONFIGDIR, 'local-repo')

	#: The ConfigParser instance
	_parser = ConfigParser()

	@staticmethod
	def load(path=CONFIGFILE):
		''' Load the config file '''
		path = abspath(path)

		if not exists(path):
			return

		try:
			Config._parser.readfp(open(path))
		except:
			raise ConfigError(_('Could not parse config file: {0}').format(path))

	@staticmethod
	def get(repo, option, default=None):
		''' Get option for a specific repo. '''
		try:
			return Config._parser.get(repo, option)
		except:
			return default

	@staticmethod
	def get_all(repo):
		''' Get all options for a specific repo '''
		try:
			return dict(Config._parser.items(repo))
		except:
			return {}

	@staticmethod
	def set(repo, option, val):
		''' Set option of speicific repo '''
		if not Config._parser.has_section(repo):
			Config._parser.add_section(repo)

		Config._parser.set(repo, option, val)

	@staticmethod
	def remove_repo(repo):
		''' Removes a repo from the config file '''
		Config._parser.remove_section(repo)

	@staticmethod
	def save(path=CONFIGFILE):
		''' Options to config file '''
		try:
			Config._parser.write(open(path, 'w'))
		except:
			raise ConfigError(_('Could not save config file: {0}').format(path))
