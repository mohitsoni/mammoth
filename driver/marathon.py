#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging

logging.basicConfig(filename='driver.log',level=logging.DEBUG)

class Marathon:
	def __init__(self, endpoint):
		if endpoint.endswith('/'):
			endpoint = endpoint[0:len(endpoint) - 1]
		self.endpoint = endpoint

	def createApp(self, app):
		logging.debug("Creating app with request: %s" % (app))
		headers = {'content-type': 'application/json', 'accept':'application/json'}
		r = requests.post(self.endpoint+'/v2/apps/', data=app, headers=headers)
		return r.status_code

	def deleteApp(self, app):
		logging.debug("Deleting app: %s" % (app))
		r = requests.delete(self.endpoint+'/v2/apps/'+app)
		return r.status_code

	def deleteApps(self):
		apps = self.getApps()

		ids = []
		for app in apps['apps']:
			ids.append(str(app['id']))

		ret = map(self.deleteApp, ids)
		return ret

	def getApp(self, app):
		logging.debug("Getting app: %s" % (app))
		r = requests.get(self.endpoint+'/v2/apps/'+app)
		if r.status_code % 200 < 100: 
			return r.json()
		else:
			return None

	def getApps(self):
		logging.debug("Getting all apps")
		r = requests.get(self.endpoint+'/v2/apps')
		if r.status_code % 200 < 100: 
			return r.json()
		else:
			return None

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("endpoint", help="Marathon endpoint")
	parser.add_argument("operation", help="Marathon operation")
	parser.add_argument("--appname", help="App Name")
	parser.add_argument("--app", help="Create App JSON")
	args = parser.parse_args()
	
	marathon = Marathon(args.endpoint)

	if (args.operation == 'getApps'):
		print marathon.getApps()
	elif (args.operation == 'getApp'):
		print marathon.getApp(args.appname)
	elif (args.operation == 'deleteApp'):
		print marathon.deleteApp(args.appname)
	elif (args.operation == 'deleteApps'):
		print marathon.deleteApps()
	elif (args.operation == 'createApp'):
		with open(args.app, 'r') as fd:
			print marathon.createApp(fd.read())
