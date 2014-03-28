#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

def computeStats(data):
	return {
		'successCount': countSuccess(data),
		'failureCount': countFailures(data),
		'averageBuildTimes': averageBuildTimes(data),
		'maxBuildTime': maxBuildTime(data),
		'minBuildTime': minBuildTime(data),
		'medianBuildTime': medianBuildTime(data),
		'percentile-95': percentile(data, 95),
		'percentile-90': percentile(data, 90),
		'percentile-80': percentile(data, 80),
		'percentile-70': percentile(data, 70),
		'percentile-60': percentile(data, 60),
		'percentile-50': percentile(data, 50),
		'percentile-40': percentile(data, 40),
		'percentile-30': percentile(data, 30),
		'failedBuilds': failedBuilds(data)
	}

def failedBuilds(data):
	return [row[0] for row in data if row[1] == 'FAILURE']

def countSuccess(data):
	return len([row[1] for row in data if row[1] == 'SUCCESS'])

def countFailures(data):
	return len([row[1] for row in data if row[1] == 'FAILURE'])

def countRunning(data):
	return 0

def averageBuildTimes(data):
	buildTimes = np.array([int(row[2]) for row in data])
	return int(buildTimes.mean()/1000)

def maxBuildTime(data):
	buildTimes = np.array([int(row[2]) for row in data])
	return int(buildTimes.max()/1000)

def minBuildTime(data):
	buildTimes = np.array([int(row[2]) for row in data])
	return int(buildTimes.min()/1000)

def medianBuildTime(data):
	buildTimes = [int(row[2]) for row in data]
	return int(np.median(np.array(buildTimes))/1000)

def percentile(data, perc):
	buildTimes = [int(row[2]) for row in data]
	return int(np.percentile(np.array(buildTimes), perc)/1000)