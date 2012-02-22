#!/usr/bin/env python3.2

import re
import sys

class Msg:
	''' A simple class with some static methods for fancy colored output '''

	@staticmethod
	def process(*args):
		''' Prints yellow bold process messages '''
		print('\033[1;33m::', ' '.join(args), '\033[0m')

	@staticmethod
	def error(*args):
		''' Prints red bold error messages '''
		print('\033[1;31m', ' '.join(args), '\033[0m', file=sys.stderr);

	@staticmethod
	def result(*args):
		''' Prints blue bold result messages '''
		print(' \033[1;34m', ' '.join(args), '\033[0m')

	@staticmethod
	def info(*args):
		''' Prints info messages '''
		print('', ' '.join(args))

	@staticmethod
	def yes(*args):
		''' Performs a simple yes/no question '''
		a = input(' ' + ' '.join(args) + '? [y|N] ')
		return False if re.match('^y(?:es)?', a, flags=re.IGNORECASE) is None else True
