#!/usr/bin/env python
import boto
import boto.ec2.cloudwatch
import sys
import os

AWS_REGION = "eu-west-1"
TOPIC = 'arn:aws:sns:eu-west-1:376907149445:alerts'

def create_status_alarm(instance_id):
    ec2_conn = boto.ec2.connect_to_region(AWS_REGION)
    cw = boto.ec2.cloudwatch.connect_to_region(AWS_REGION)

    reservations = ec2_conn.get_all_instances(filters = {'instance-id': instance_id})
    if reservations and reservations[0].instances:
        instance = reservations[0].instances[0]
        instance_name = instance.tags['Name']
    else:
        print "Invalid instance-id!"
        sys.exit(1)
    metric = cw.list_metrics(dimensions={'InstanceId':instance_id},metric_name="CPUUtilization")[0]

    metric.create_alarm(
        name = instance_name + "-cpu",
        statistic = 'Average',
        comparison = '>=',
        description = 'CPU alert for %s %s' % (instance_id, instance_name),
        threshold = 70,
        period = 300,
        evaluation_periods = 2,
        dimensions = {'InstanceId':instance_id},
        alarm_actions = [TOPIC],
        ok_actions = [TOPIC],
        insufficient_data_actions = [TOPIC])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: create_status_alarm.py <instanceid>"
        sys.exit(2)
    create_status_alarm(sys.argv[1])
