# aur.py
# vim:ts=4:sw=4:noexpandtab

from urllib.request import urlopen
from urllib.parse import urlencode
from json import loads as parse
from threading import Thread, Lock

from localrepo.utils import LocalRepoError

class AurError(LocalRepoError):
	''' Handles Aur errors '''
	pass


class AurRequest(Thread):

	_results = {}
	_errors = []
	_lock = Lock()

	@staticmethod
	def clear():
		with AurRequest._lock:
			AurRequest._results = {}
			AurRequest._errors = []

	@staticmethod
	def results():
		with AurRequest._lock:
			return AurRequest._results

	@staticmethod
	def errors():
		with AurRequest._lock:
			return AurRequest._errors

	def __init__(self, request, data):
		Thread.__init__(self)
		self._request = request
		self._data = data

	def run(self):
		try:
			result = Aur.request(self._request, self._data)
		except AurError as e:
			with AurRequest._lock:
				AurRequest._errors.append(e)
		else:
			with AurRequest._lock:
				AurRequest._results.update(result)


class Aur:
	''' A class that manages request to the AUR '''

	#: Uri of the AUR
	HOST = 'https://aur.archlinux.org'

	#: Uri of the AUR API
	API = '/rpc.php'

	#: Max number of packages per request
	MAX = 50

	#: Translations from AUR to localrepo
	TRANS = {'Name': 'name',
	         'Version': 'version',
	         'URLPath': lambda p: ('uri', Aur.HOST + p)}

	@staticmethod
	def decode_info(info):
		''' Turns an AUR info dict into a localrepo style package info  dict '''
		return dict(t(info[k]) if callable(t) else (t, info[k]) for k, t in Aur.TRANS.items())

	@staticmethod
	def request(request, data):
		''' Performs the AUR API request '''
		query = [('type', request)]

		if type(data) is str:
			query.append(('arg', data))
		else:
			query += [('arg[]', d) for d in data]

		try:
			res = urlopen(Aur.HOST + Aur.API + '?' + urlencode(query))
		except:
			raise AurError(_('Could not reach the AUR'))

		if res.status is not 200:
			raise AurError(_('AUR responded with error: {0}').format(res.reason))

		try:
			info = parse(res.read().decode('utf8'))
			error = info['type'] == 'error'
			results = info['results']
		except:
			raise AurError(_('AUR responded with invalid data'))

		if error:
			raise AurError(_('AUR responded with error: {0}').format(results))

		try:
			if type(results) is dict:
				return Aur.decode_info(results)

			return dict((i['Name'], Aur.decode_info(i)) for i in results)
		except:
			raise AurError(_('AUR responded with invalid data'))

	@staticmethod
	def package(name):
		''' Asks the AUR for informations about a single package '''
		return Aur.request('info', name)

	@staticmethod
	def packages(names):
		''' Asks the AUR for informations about multiple packages '''
		AurRequest.clear()
		requests = []

		for i in range(0, len(names), Aur.MAX):
			request = AurRequest('multiinfo', names[i:i + Aur.MAX])
			requests.append(request)
			request.start()

		for r in requests:
			r.join()

		return AurRequest.results(), AurRequest.errors()

	@staticmethod
	def search(q):
		''' Searches the AUR for packages '''
		return Aur.request('search', q)
