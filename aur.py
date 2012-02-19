#!/usr/bin/env python3.2

import json
from urllib import request

class Aur:
	HOST = 'http://aur.archlinux.org'
	API = '/rpc.php?type=multiinfo'

	@staticmethod
	def package_infos(packages):
		data = ''

		for pkg in packages:
			data += '&arg[]=' + pkg

		try:
			res = request.urlopen(Aur.HOST + Aur.API + data)
		except:
			raise Exception('Could not reach AUR API')

		if res.status is not 200:
			raise Exception('AUR responded with error: {0}'.format(res.reason))

		infos = json.loads(res.read().decode('utf8'))

		if infos['type'] == 'error':
			raise Exception('AUR responded with error: {0}'.format(infos['results']))

		packages = {}

		for pkg in infos['results']:
			packages[pkg['Name']] = {'version': pkg['Version'], 'url': Aur.HOST + pkg['URLPath']}

		return packages
