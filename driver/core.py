#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import glob
import time
import uuid
import pickle
import config as dconfig
import logging
import requests
import grequests
import marathon
import argparse
import functools
import jenkinsapi
import multiprocessing

logging.basicConfig(filename='driver.log',level=logging.DEBUG)

# Constants Start
MARATHON_URL = ''
APP_PREFIX = 'test_jenkins_master_'
JOB_PREFIX = 'job_'
JENKINS_JOB_NAME='build'
JENKINS_JOB_CONFIG = 'echojob'

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'fixtures'))+"/"
APP_FIXTURES = "apps/"
JOB_FIXTURES = "jobs/"
JENKINS_FIXTURE= "jenkins"
WORKERS = multiprocessing.cpu_count()
NUM_JENKINS_JOBS = 2
NUM_JOBS_TO_TRIGGER = 2
# Constants End

def _init_config(driverConfig):
	global MARATHON_URL
	global APP_PREFIX
	global JOB_PREFIX
	global JENKINS_JOB_NAME
	global JENKINS_JOB_CONFIG
	global NUM_JENKINS_JOBS
	global NUM_JOBS_TO_TRIGGER

	MARATHON_URL = driverConfig['marathon_url']
	APP_PREFIX = driverConfig['app_prefix']
	JOB_PREFIX = driverConfig['job_prefix']
	JENKINS_JOB_NAME = driverConfig['jenkins_job_name']
	JENKINS_JOB_CONFIG = driverConfig['jenkins_job_config']
	NUM_JENKINS_JOBS = int(driverConfig['num_jenkins_jobs'])
	NUM_JOBS_TO_TRIGGER = int(driverConfig['num_jobs_to_trigger'])

def check_jenkins(jenkins_url):
	if not jenkins_url:
		return False

	RETRY_COUNT = 5
	RETRY_INTERVAL = 5 # seconds

	response = None
	while RETRY_COUNT > 0:
		try:
			logging.debug("Checking jenkins: %s, tries left: %s" % (jenkins_url, str(RETRY_COUNT)))
			response = requests.head(jenkins_url)

			if (response.status_code % 200 < 100):
				return True
		except:
			logging.error('Timeout for: %s | count: %s' % (jenkins_url, str(RETRY_COUNT)))

		time.sleep(RETRY_INTERVAL)

		RETRY_COUNT = RETRY_COUNT - 1

	return False

def get_host_port(master_name):
	mclient = marathon.Marathon(MARATHON_URL)
	response = mclient.getApp(master_name)
	if response:
		tasks = response['app']['tasks']
		if tasks and len(tasks) > 0:
			host = tasks[0]['host']
			port = str(tasks[0]['ports'][0])
			jenkins_url = "http://"+host+":"+port
			return jenkins_url

	return None

def create_jenkins_master(master_name, jobConfig):
	logging.debug('Creating jenkins master: %s' %(master_name))

	app_json = load_fixture(FIXTURES_DIR+APP_FIXTURES+JENKINS_FIXTURE)
	app_json = app_json % (master_name, master_name)

	mclient = marathon.Marathon(MARATHON_URL)
	status = mclient.createApp(app_json)

	# time.sleep(120)

	jenkins_url = None
	
	return {'name': master_name, 'url': jenkins_url}

def poll(master):
	master_name = master['name']
	jenkins_url = None
	MAX_ATTEMPTS = 20
	for i in range(MAX_ATTEMPTS):
		jenkins_url = get_host_port(master_name)

		if not jenkins_url:
			time.sleep(5)
		else:
			break

		logging.debug('Attempt [%s] | master: %s | url: %s' % (i, master_name, jenkins_url))	

	return {'name': master_name, 'url': jenkins_url}

def create_jenkins_job(job_name, master_url, job_config_url):
	logging.debug('Creating jenkins job: %s with job config: %s on master: %s' % (job_name, job_config_url, master_url))
	config = load_fixture(FIXTURES_DIR+JOB_FIXTURES+job_config_url)

	if config:
		logging.debug(config)

		headers = {'content-type': 'application/xml', 'accept':'application/xml'}
		post_url = str(master_url)+"/createItem?name="+str(job_name)
		
		try:
			r = requests.post(post_url, data=config, headers=headers)

			if r.status_code % 200 < 100: 
				return master_url+'/job/'+job_name
			else:
				return None
		except Exception, err:
			logging.exception('Error in create_jenkins_job()')
			return None

def create_jenkins_jobs(master):
	name = master['name']
	url = master['url']

	status = check_jenkins(url)

	if not status:
		return None

	job_names = [JENKINS_JOB_NAME + str(i) for i in range(NUM_JENKINS_JOBS)]

	jobs = map(functools.partial(create_jenkins_job, master_url=url, job_config_url=JENKINS_JOB_CONFIG), job_names)

	return {'name': name, 'url': url, 'jobs': jobs}

def trigger_build(job_url):
	logging.debug('Triggering build for job: %s' % (job_url))
	
	headers = {'content-type': 'application/xml', 'accept':'application/xml'}
	
	build_url = job_url+"/build"

	r = requests.post(build_url, headers=headers)

	time.sleep(1)

	if r.status_code % 200 < 100 or r.status_code % 300 < 100:
		return True
	else:
		return False	

def delete_jenkins_master(master_name):
	logging.debug('Deleting jenkins master: %s' % (master_name))
	mclient = marathon.Marathon(MARATHON_URL)
	mclient.deleteApp(master_name)

def initialize(driverConfig, config, num_apps):
	try:
		pool = multiprocessing.Pool(WORKERS)
		
		# Create jenkins masters
		master_names = [APP_PREFIX + str(uuid.uuid4()) for i in xrange(num_apps)]
		created_masters = pool.map(functools.partial(create_jenkins_master, jobConfig=config), master_names)
		logging.debug("Created masters: %s" % (created_masters))

		# Give marathon some time, before polling for host:port
		time.sleep(60)

		polled_masters = pool.map(poll, created_masters)
		logging.debug("Polled masters: %s" % (polled_masters))

		# Creating jobs
		created_jobs = pool.map(create_jenkins_jobs, polled_masters)

		logging.debug("Created Jobs: %s" % (created_jobs))

		for created_job in created_jobs:
			if created_job:
				name = created_job['name']
				url = created_job['url']
				jobs = created_job['jobs']

				config.addMaster(name, url)

				for job in jobs:
					config.addJob(name, job)
		
	except Exception, err:
		logging.exception('Error in initialize()')

def trigger(driverConfig, jobConfig):
	jobs_list_list = jobConfig.getJobs()
	headers = {'content-type': 'application/xml', 'accept':'application/xml'}
	jobs_to_trigger = [grequests.post(job+'/build', headers=headers) for job_list in jobs_list_list.values() for job in job_list] * NUM_JOBS_TO_TRIGGER

	grequests.map(jobs_to_trigger)

def cleanup(driverConfig, jobConfig, jobConfigFile):
	masters = jobConfig.getMasterNames()
	map(delete_jenkins_master, masters)
	os.remove(jobConfigFile)

def save_config(driverConfig, config_file, config):
	with open(config_file, 'wb') as fd:
		pickle.dump(config, fd)

def load_config(config_file):
	with open(config_file, 'r') as fd:
		return pickle.load(fd)

def load_fixture(fixture_path):
	logging.debug('Loading fixture: %s' % (fixture_path))
	with open(fixture_path, "r") as fd:
		return fd.read()

# Collect statistics
def captureClusterStatus(driverConfig, config):
	mastersConfig = config.getMasters()

	masters = [{'name':name, 'url': mastersConfig[name]} for name in mastersConfig.keys()]
	logging.debug('Capturing statuses for masters: %s' % masters)

	pool = multiprocessing.Pool(WORKERS)
	status = pool.map(captureStatus, masters)

	return status

def captureStatus(master):
	name = master['name']
	url = master['url']
	j = jenkinsapi.jenkins.Jenkins(url)

	# Get jobs
	jobs = j.keys()

	jobStatus = {'name':name, 'url':url, 'jobs': []}

	if jobs:
		# Get build status and times
		for job in jobs:
			buildIds = j[job].get_build_ids()
			builds = []
			for buildId in buildIds:
				build = j[job].get_build(int(buildId))
				duration = build._data['duration']
				status = build.get_status()
				buildStatus = {'buildId':str(buildId), 'duration':str(duration), 'status': status}

				builds.append(buildStatus)

			jobStatus['jobs'].append({'job':job, 'builds':builds})
	logging.debug(jobStatus)

	return jobStatus

def flattenStats(driverConfig, stats):
	flatstats=[]

	for s in stats:
		url = s['url']

		for job in s['jobs']:
			jobUrl = url + '/job/' + job['job']

			for build in job['builds']:
				buildUrl = jobUrl + '/' + build['buildId']
				status = str(build['status'])
				duration = build['duration']

				flatstats.append((buildUrl, status, duration))

	return flatstats

def getAllJobs():
	mclient = marathon.Marathon(MARATHON_URL)
	apps = mclient.getApps()
	for app in apps['apps']:
		a = mclient.getApp(app['id'])
		host = a['app']['tasks'][0]['host']
		port = a['app']['ports'][0]
		url = 'http://' + host + ':' + str(port)
		master = {'name': id, 'url': url}
		print captureStatus(master)

if __name__ == '__main__':
	getAllJobs()