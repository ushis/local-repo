# error.py
# vim:ts=4:sw=4:noexpandtab

from localrepo.utils import Msg

class LocalRepoError(Exception):
	''' Base exception used by all local-repo errors '''

	#: If true, all error messages will be printed immediately
	debug = False

	def __init__(self, msg):
		''' Sets the error message '''
		self._msg = msg

		if LocalRepoError.debug:
			Msg.debug(msg)

	@property
	def message(self):
		''' Returns the error message '''
		return self._msg

	def __str__(self):
		''' Returns the error message '''
		return self._msg
