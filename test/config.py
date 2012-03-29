# test/config.py
# vim:ts=4:sw=4:noexpandtab

import sys

from os import remove
from os.path import join
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from unittest import TestCase, main

if '..' not in sys.path:
	sys.path.append('..')

from localrepo.config import Config


class ConfigTest(TestCase):

	CONFIG = '''# local-repo-test-config
[all]
sign = no
signdb = off
log = .log

[test]
path = {path}
sign = yes
log = .repo/log
buildlog = /path/to/buildlog
no-aur-upgrade = pkg1 pkg2
	pkg3'''

	def setUp(self):
		self.repo = mkdtemp(prefix='local-repo-test-repo-')
		l, self.conf = mkstemp(prefix='local-repo-test-conf-')

		with open(self.conf, 'w') as f:
			f.write(ConfigTest.CONFIG.format(path=self.repo))

		Config.init('test', path=self.conf)

	def tearDown(self):
		rmtree(self.repo)
		remove(self.conf)

	def test_normalize_path(self):
		equal = [join(self.repo, e) for e in ('test.db.tar.gz', 'test.db', '')]
		equal.append(self.repo)

		for e in equal:
			self.assertEqual(self.repo, Config.normalize_path(e))

	def test_find_repo_by_path(self):
		self.assertEqual('test', Config.find_repo_by_path(self.repo))
		self.assertEqual('/home', Config.find_repo_by_path('/home/something'))

	def test_get(self):
		self.assertIs(True, Config.get('sign'))
		self.assertIs(False, Config.get('signdb'))
		self.assertEqual(self.repo, Config.get('path'))
		self.assertEqual('.repo/log', Config.get('log'))
		self.assertEqual('/path/to/buildlog', Config.get('buildlog'))
		self.assertEqual(['pkg1', 'pkg2', 'pkg3'], Config.get('no-aur-upgrade'))
		self.assertIs(None, Config.get('pkgbuild'))
		self.assertEqual('default', Config.get('pkgbuild', 'default'))

	def test_set(self):
		Config.set('hello', 'world')
		self.assertEqual('world', Config.get('hello'))
		Config.set('sign', False)
		self.assertIs(False, Config.get('sign'))
		Config.set('something', True)
		self.assertEqual('yes', Config.get('something'))
		Config.set('no-aur-upgrade', ['pkg1', 'pkg2'])
		self.assertEqual(['pkg1', 'pkg2'], Config.get('no-aur-upgrade'))
		Config.set('something', [1, 2, 3])
		self.assertEqual('1 2 3', Config.get('something'))

	def test_remove(self):
		Config.remove('sign')
		self.assertIs(False, Config.get('sign'))
		Config.remove('log')
		self.assertEqual('.log', Config.get('log'))
		Config.remove('buildlog')
		self.assertIs(None, Config.get('buildlog'))
		Config.remove('no-aur-upgrade')
		self.assertIs(None, Config.get('no-aur-upgrade'))

	def test_save(self):
		Config.init('test2', path=self.conf)
		Config.set('path', self.repo)
		Config.set('sign', True)
		Config.set('log', '/some/fancy/path')
		Config.save(path=self.conf)
		Config.init('test2', path=self.conf)
		self.assertEqual(self.repo, Config.get('path'))
		self.assertIs(True, Config.get('sign'))
		self.assertEqual('/some/fancy/path', Config.get('log'))

if __name__ == '__main__':
	main()
