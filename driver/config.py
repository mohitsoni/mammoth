#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ConfigParser

CONFIG_SECTION='mammoth'

class JobConfig:
	# List of all created masters
	masters = {}

	# Dictionary of master and created jobs
	jobs = {}

	def __init__(self, masters={}, jobs={}):
		self.masters = masters
		self.jobs = jobs

	def getMasters(self):
		return self.masters

	def getMasterNames(self):
		return self.masters.keys()

	def getMasterUrls(self):
		return self.masters.values()

	def addMaster(self, master_name, master_url):
		self.masters[master_name] = master_url

	def getJobs(self):
		return self.jobs

	def addJob(self, master_name, job_url):
		if master_name in self.jobs:
			self.jobs[master_name].append(job_url)
		else:
			self.jobs[master_name] = [job_url]

	def __repr__(self):
		return str(self.__dict__)

# Load configuration and returns items from the specified section
def loadConfig(location='driver.cfg', section=CONFIG_SECTION):
	if os.path.exists(location):
		config = ConfigParser.SafeConfigParser(allow_no_value=True)
		config.readfp(open(location))
		items = config.items(section)

		config = {}

		for item in items:
			config[item[0]] = item[1]

		return config