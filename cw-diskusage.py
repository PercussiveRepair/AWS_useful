#!/usr/bin/env python
'''
Send disk usage metrics to Amazon CloudWatch
This is intended to run on an Amazon EC2 instance and requires an IAM
role allowing to write CloudWatch metrics. Alternatively, you can create
a boto credentials file and rely on it instead.
Original idea based on https://github.com/colinbjohnson/aws-missing-tools
'''
import sys
import commands
from boto.ec2 import cloudwatch
from boto.utils import get_instance_metadata
def collect_disk_usage(mount_point='/'):
    mounts = commands.getoutput('mount')
    usage = {}
    for l in mounts.splitlines():
        if l.startswith('/dev'):
            mount = l.split()[0]
            usage[mount] = commands.getoutput("USAGE=`df -h {} | tail -1 | awk '{{print $5; }}'` ; echo ${{USAGE%?}}".format(mount))
    return usage
def send_multi_metrics(instance_id, region, metrics, namespace='EC2/Disk',
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
    disk_usage = collect_disk_usage()
    metrics = disk_usage
    send_multi_metrics(instance_id, region, metrics)