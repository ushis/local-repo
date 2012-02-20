#!/usr/bin/env python3.2

from urllib.request import urlopen
import json

class Aur:
	HOST = 'http://aur.archlinux.org'
	API = '/rpc.php'

	@staticmethod
	def decode_info(info):
		return {'name': info['Name'], 'version': info['Version'], 'uri': AUR.HOST + info['URLPath']}

	@staticmethod
	def request(request, data):
		uri = '{0}{1}?type={2}'

		if type(data) in [dict, list]:
			uri += '&arg[]=' + '&arg[]='.join(data)
		else:
			uri += '&arg=' + str(data)

		try:
			res = urlopen(uri)
		except:
			raise Exception('Could not reach the AUR')

		if res.status is not 200:
			raise Exception('AUR responded with error: {0}'.format(res.reason))

		try:
			infos = json.loads(res.read().decode('utf8'))
		except:
			raise Exception('AUR responded with invalid data')

		if 'type' not in infos or 'results' not in infos:
			raise Exception('AUR reponded with invalid data')

		if infos['type'] == 'error':
			raise Exception('AUR responded with error: {0}'.format(infos['results']))

		try:
			if type(infos['results']) is dict:
				return Aur.decode(infos['result'])

			results = {}

			for info in infos:
				results[info['Name']] = Aur.decode(info)

			return results
		except:
			raise Exception('AUR responded with invalid data')

	@staticmethod
	def package(name):
		return Aur.request('info', name)

	@staticmethod
	def packages(names):
		return Aur.request('multiinfo', names)

	@staticmethod
	def search(q):
		return Aur.request('search', q)
