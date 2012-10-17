# test/pacman.py
# vim:ts=4:sw=4:noexpandtab

import sys
from unittest import TestCase, main

if '..' not in sys.path:
	sys.path.append('..')

from localrepo.pacman import Pacman
from localrepo.config import Config

class PacmanTest(TestCase):

	cmd = ''

	@staticmethod
	def call(cmd):
		PacmanTest.cmd = ' '.join(cmd)

	def setUp(self):
		Pacman.call = PacmanTest.call

	def test_install(self):
		Pacman.install(['pkg1', 'pkg2'], as_deps=True)

		cmds = ['/usr/bin/sudo /usr/bin/pacman -Sy pkg1 pkg2 --asdeps',
		        '/bin/su -c \'/usr/bin/pacman -Sy pkg1 pkg2 --asdeps\'']

		self.assertIn(PacmanTest.cmd, cmds)

	def test_check_deps(self):
		self.assertEqual(['pkg1', 'pkg2'], Pacman.check_deps(['pkg1', 'pkg2', 'pacman']))
		self.assertEqual([], Pacman.check_deps(['pacman']))
		self.assertEqual([], Pacman.check_deps([]))

	def test_make_package(self):
		Config.init('mytestrepo')
		Config.set('sign', False)
		Config.set('buildlog', '')
		Pacman.make_package('/tmp')
		self.assertEqual('/usr/bin/makepkg -d --nosign', PacmanTest.cmd)
		Pacman.make_package('/tmp', force=True)
		self.assertEqual('/usr/bin/makepkg -d -f --nosign', PacmanTest.cmd)
		Config.set('buildlog', '/some/path')
		Pacman.make_package('/tmp')
		self.assertEqual('/usr/bin/makepkg -d -L -m --nosign', PacmanTest.cmd)
		Config.set('sign', True)
		Pacman.make_package('/tmp')
		self.assertEqual('/usr/bin/makepkg -d -L -m --sign', PacmanTest.cmd)

	def test_repo_add(self):
		Config.init('mytestrepo')
		Config.set('signdb', False)
		Pacman.repo_add('my.db.tar.gz', ['pkg1', 'pkg2'])
		self.assertEqual('/usr/bin/repo-add my.db.tar.gz pkg1 pkg2', PacmanTest.cmd)
		Config.set('signdb', True)
		Pacman.repo_add('db', ['pkg1'])
		self.assertEqual('/usr/bin/repo-add db pkg1 --verify --sign', PacmanTest.cmd)

	def test_repo_remove(self):
		Config.init('mytestrepo')
		Config.set('signdb', False)
		Pacman.repo_remove('my.db.tar.gz', ['pkg1', 'pkg2'])
		self.assertEqual('/usr/bin/repo-remove my.db.tar.gz pkg1 pkg2', PacmanTest.cmd)
		Config.set('signdb', True)
		Pacman.repo_remove('db', ['pkg1'])
		self.assertEqual('/usr/bin/repo-remove db pkg1 --verify --sign', PacmanTest.cmd)


if __name__ == '__main__':
	main()
