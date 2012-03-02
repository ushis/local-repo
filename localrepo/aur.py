# aur.py
# vim:ts=4:sw=4:noexpandtab

from urllib.request import urlopen
import json

class Aur:
	''' A class that manages request to the AUR '''

	#: Uri of the AUR
	HOST = 'http://aur.archlinux.org'

	#: Uri of the AUR API
	API = '/rpc.php'

	@staticmethod
	def decode_info(info):
		''' Turns an AUR info dict into a localrepo style package info  dict '''
		return {'name': info['Name'], 'version': info['Version'], 'uri': Aur.HOST + info['URLPath']}

	@staticmethod
	def request(request, data):
		''' Performs the AUR API request '''
		uri = '{0}{1}?type={2}'.format(Aur.HOST, Aur.API, request)

		if type(data) is str:
			uri += '&arg=' + data
		else:
			uri += '&arg[]=' + '&arg[]='.join(data)

		try:
			res = urlopen(uri)
		except:
			raise Exception(_('Could not reach the AUR'))

		if res.status is not 200:
			raise Exception(_('AUR responded with error: {0}').format(res.reason))

		try:
			infos = json.loads(res.read().decode('utf8'))
		except:
			raise Exception(_('AUR responded with invalid data'))

		if 'type' not in infos or 'results' not in infos:
			raise Exception(_('AUR responded with invalid data'))

		if infos['type'] == 'error':
			raise Exception(_('AUR responded with error: {0}').format(infos['results']))

		try:
			if type(infos['results']) is dict:
				return Aur.decode_info(infos['results'])

			return dict((i['Name'], Aur.decode_info(i)) for i in infos['results'])
		except:
			raise Exception(_('AUR responded with invalid data'))

	@staticmethod
	def package(name):
		''' Asks the AUR for informations about a single package '''
		return Aur.request('info', name)

	@staticmethod
	def packages(names):
		''' Asks the AUR for informations about multiple packages '''
		return Aur.request('multiinfo', names)

	@staticmethod
	def search(q):
		''' Searches the AUR for packages '''
		return Aur.request('search', q)
