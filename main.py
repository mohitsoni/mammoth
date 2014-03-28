#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import argparse
import driver.core as dcore
import driver.config as dconfig
import driver.stats as dstats
import multiprocessing

# Configure logging
logging.basicConfig(filename='driver.log',level=logging.DEBUG)

def initializeParser():
	parser = argparse.ArgumentParser()
	parser.add_argument("command", 
		help="""
		start: Initialize the load testing;
		status: Gets the status of active load testing;
		stop: Stops the active load testing, and performs cleanup
		""")
	parser.add_argument("name", 
		help="Name of load testing job")
	parser.add_argument("--count", 
		help="Count of items, in case of start it's the number of jenkins instances")
	parser.add_argument("--config", 
		help="Location of driver config, by defaults loads driver.cfg file in current directory.")

	return parser

def fetchArguments(parser):
	args = parser.parse_args()
	
	logging.debug("Arguments: %s" % (args))

	jobConfigFile = args.name
	command = args.command
	count = args.count
	driver_config = args.config

	logging.debug("Job name: %s" % (jobConfigFile))
	logging.debug("Command: %s" % (command))
	logging.debug("Driver config: %s" % (driver_config))

	return (jobConfigFile, command, count, driver_config)

def main():
	jobConfig = None
	jobConfigFile = None
	driverConfig = None
	driverConfigFile = None

	parser = initializeParser()
	(jobConfigFile, command, count, driverConfigFile) = fetchArguments(parser)

	if not driverConfigFile:
		driverConfigFile='driver.cfg'

	driverConfig = dconfig.loadConfig(driverConfigFile)
	logging.debug(driverConfig)
	dcore._init_config(driverConfig)

	if (command == 'start'):
		if os.path.isfile(jobConfigFile):
			logging.error('Job with name: %s, already started. Cannot start a new job with same name.' % (jobConfigFile))
			sys.exit(1)

		num_apps = 1
		if count:
			num_apps = int(count)
		jobConfig = dconfig.JobConfig()
		dcore.initialize(driverConfig, jobConfig, num_apps)
		dcore.save_config(driverConfig, jobConfigFile, jobConfig)
	elif (command == 'trigger'):
		jobConfig = dcore.load_config(jobConfigFile)
		# While collecting jenkins status, always query marathon for correct URL.
		logging.debug(jobConfig)

		dcore.trigger(driverConfig, jobConfig)
	elif (command == 'status'):
		jobConfig = dcore.load_config(jobConfigFile)
		
		# While collecting jenkins status, always query marathon for correct URL.
		logging.debug(jobConfig)
		status = dcore.captureClusterStatus(driverConfig, jobConfig)
		fstatus = dcore.flattenStats(driverConfig, status)
		stats = dstats.computeStats(fstatus)
		jstr = json.dumps(stats)
		print jstr
		logging.info(jstr)

		with open(jobConfigFile+".json", 'w') as fd:
			fd.write(jstr)
	elif (command == 'stop'):
		jobConfig = dcore.load_config(jobConfigFile)
		
		logging.debug(jobConfig)
		
		dcore.cleanup(driverConfig, jobConfig, jobConfigFile)
	else:
		pass

if __name__ == '__main__':
	main()