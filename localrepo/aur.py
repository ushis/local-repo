# aur.py
# vim:ts=4:sw=4:noexpandtab

from urllib.request import urlopen
from urllib.parse import urlencode
from json import loads as parse
from threading import Thread

from localrepo.utils import LocalRepoError

class AurError(LocalRepoError):
	''' Handles AUR errors '''
	pass


class AurRequestError(AurError):
	''' Handles AUR request errors '''
	pass


class AurRequest(Thread):
	''' Handles parallel AUR requests '''

	#: Uri of the AUR
	HOST = 'https://aur.archlinux.org'

	#: Uri of the AUR API
	API = '/rpc.php'

	#: Max number of packages per request
	MAX = 50

	#: Translations from AUR to localrepo
	TRANS = {'Name': 'name',
	         'Version': 'version',
	         'URLPath': lambda p: ('uri', AurRequest.HOST + p)}

	@staticmethod
	def decode_result(res):
		''' Turns an AUR info dict into a localrepo style package info  dict '''
		return dict(t(res[k]) if callable(t) else (t, res[k]) for k, t in AurRequest.TRANS.items())

	@staticmethod
	def forge(request, data):
		''' Splits a request in to smaller ones - if needed - and sends them to the AUR '''
		requests = []

		for i in range(0, len(data), AurRequest.MAX):
			r = AurRequest(request, data[i:i + AurRequest.MAX])
			requests.append(r)
			r.start()

		results, errors = {}, []

		for r in requests:
			r.join()
			results.update(r.results)

			if r.error is not None:
				errors.append(r.error)

		return results, errors

	def __init__(self, request, data):
		''' Sets the request type and the data '''
		super().__init__()
		self._request = request
		self._data = data
		self._results = {}
		self._error = None

	@property
	def results(self):
		''' Returns the results '''
		return self._results

	@property
	def error(self):
		''' Returns the error '''
		return self._error

	def run(self):
		''' Thread entry point'''
		try:
			self._send()
		except AurRequestError as e:
			self._error = e

	def _send(self):
		''' Performs the AUR API request '''
		if len(self._data) is 0:
			return

		query = [('type', self._request)]

		if self._request in ('info', 'search'):
			query.append(('arg', self._data[0]))
		else:
			query += [('arg[]', d) for d in self._data]

		try:
			res = urlopen(AurRequest.HOST + AurRequest.API + '?' + urlencode(query))
		except:
			raise AurRequestError(_('Could not reach the AUR'))

		if res.status is not 200:
			raise AurRequestError(_('AUR responded with error: {0}').format(res.reason))

		try:
			info = parse(res.read().decode('utf8'))
			error = info['type'] == 'error'
			results = info['results']
		except:
			raise AurRequestError(_('AUR responded with invalid data'))

		if error:
			raise AurRequestError(_('AUR responded with error: {0}').format(results))

		if type(results) is dict:
			results = [results]

		try:
			self._results = dict((r['Name'], AurRequest.decode_result(r)) for r in results)
		except:
			raise AurRequestError(_('AUR responded with invalid data'))


class Aur:
	''' A class that manages request to the AUR '''

	@staticmethod
	def package(name):
		''' Asks the AUR for informations about a single package '''
		return AurRequest.forge('info', [name])

	@staticmethod
	def packages(names):
		''' Asks the AUR for informations about multiple packages '''
		return AurRequest.forge('multiinfo', names)

	@staticmethod
	def search(q):
		''' Searches the AUR for packages '''
		return AurRequest.forge('search', [q])
