#!/usr/bin/env python3.2

import re
import sys

class Msg:
	@staticmethod
	def process(*args):
		print('\033[1;33m::', ' '.join(args), '\033[0m')

	@staticmethod
	def error(*args):
		print('\033[1;31m', ' '.join(args), '\033[0m', file=sys.stderr);

	@staticmethod
	def result(*args):
		print(' \033[1;34m', ' '.join(args), '\033[0m')

	@staticmethod
	def info(*args):
		print('', ' '.join(args))

	@staticmethod
	def yes(*args):
		a = input(' ' + ' '.join(args) + '? [y|N] ')

		if re.match('^y(?:es)?', a, flags=re.IGNORECASE) is None:
			return False

		return True
