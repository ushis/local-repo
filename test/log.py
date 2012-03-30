# test/log.py
# vim:ts=4:sw=4:noexpandtab

import sys

from os.path import basename, join, isdir, isfile
from tempfile import mkdtemp, mkstemp
from shutil import rmtree
from unittest import TestCase, main

if '..' not in sys.path:
	sys.path.append('..')

from localrepo.config import Config
from localrepo.log import Log, BuildLog, PkgbuildLog


class LogTest(TestCase):

	def setUp(self):
		self.repo = mkdtemp(prefix='local-repo-test-repo-')
		self.log = join(self.repo, '.data', 'log', 'some', 'path')
		self.buildlog = join(self.repo, '.data', 'buildlog', 'path', 'yay')
		self.pkgbuild = join(self.repo, '.data', 'pkgbuild', 'test')
		Config.init('logtest')
		Config.set('path', self.repo)
		Config.set('log', self.log)
		Config.set('buildlog', self.buildlog)
		Config.set('pkgbuild', self.pkgbuild)

	def tearDown(self):
		rmtree(self.repo)

	def test_log(self, error=False):
		msgs = ['Hello!', 'This is just a test...', 'Everything is fine... hopefully']
		Log.init(self.repo)

		for msg in msgs:
			Log.error(msg) if error else Log.log(msg)

		Log.close()

		with open(self.log) as f:
			i = 0
			p = '^\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}\] '

			if error:
				p += '\[\w+\] '

			for line in f:
				self.assertRegex(line, p + msgs[i] + '\n')
				i += 1

	def test_error(self):
		self.test_log(error=True)

	def test_store_buildlog(self):
		BuildLog.init(self.repo)

		for pkg in ['pkg1', 'pkg2', 'pkg1']:
			l, f = mkstemp(prefix='local-repo-test-buildlog-file-')
			BuildLog.store(pkg, f)
			self.assertIs(True, isfile(join(self.buildlog, pkg, basename(f))))

	def test_pkgbuild_log_dir(self):
		PkgbuildLog.init(self.repo)
		self.assertEqual(join(self.pkgbuild, 'pkgname'), PkgbuildLog.log_dir('pkgname'))

	def test_store_and_load__pkgbuild(self):
		PkgbuildLog.init(self.repo)

		for pkg in ['pkg1', 'pkg2', 'pkg1']:
			tmpdir = mkdtemp(prefix='local-repo-test-pkgbuild-dir-')
			l, f = mkstemp(prefix='local-repo-test-pkgbuild-file-', dir=tmpdir)
			PkgbuildLog.store(pkg, tmpdir)
			rmtree(tmpdir)
			self.assertIs(True, isfile(join(self.pkgbuild, pkg, basename(f))))

		tmpdir = mkdtemp(prefix='local-repo-test-pkgbuild-dir-')

		for pkg in ['pkg1', 'pkg2', 'pkg1']:
			PkgbuildLog.load(pkg, join(tmpdir, pkg))
			self.assertIs(True, isdir(join(tmpdir, pkg)))

		rmtree(tmpdir)


if __name__ == '__main__':
	main()
