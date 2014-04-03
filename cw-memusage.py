#!/usr/bin/env python
'''
Send memory usage metrics to Amazon CloudWatch

This is intended to run on an Amazon EC2 instance and requires an IAM
role allowing to write CloudWatch metrics. Alternatively, you can create
a boto credentials file and rely on it instead.

Original idea based on https://github.com/colinbjohnson/aws-missing-tools
'''

import sys
import re
from boto.ec2 import cloudwatch
from boto.utils import get_instance_metadata

def collect_memory_usage():
    meminfo = {}
    pattern = re.compile('([\w\(\)]+):\s*(\d+)(:?\s*(\w+))?')
    with open('/proc/meminfo') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                # For now we don't care about units (match.group(3))
                meminfo[match.group(1)] = float(match.group(2))
    return meminfo

def send_multi_metrics(instance_id, region, metrics, namespace='EC2/Memory',
                        unit='Percent'):
    '''
    Send multiple metrics to CloudWatch
    metrics is expected to be a map of key -> value pairs of metrics
    '''
    cw = cloudwatch.connect_to_region(region)
    cw.put_metric_data(namespace, metrics.keys(), metrics.values(),
                       unit=unit,
                       dimensions={"InstanceId": instance_id})

if __name__ == '__main__':
    metadata = get_instance_metadata()
    instance_id = metadata['instance-id']
    region = metadata['placement']['availability-zone'][0:-1]
    mem_usage = collect_memory_usage()

    mem_free = mem_usage['MemFree'] + mem_usage['Buffers'] + mem_usage['Cached']
    mem_used = mem_usage['MemTotal'] - mem_free
    if mem_usage['SwapTotal'] != 0 :
        swap_used = mem_usage['SwapTotal'] - mem_usage['SwapFree'] - mem_usage['SwapCached']
        swap_percent = swap_used / mem_usage['SwapTotal'] * 100
    else:
        swap_percent = 0

    metrics = {'MemUsage': mem_used / mem_usage['MemTotal'] * 100,
               'SwapUsage': swap_percent }

    send_multi_metrics(instance_id, region, metrics)
