#! /usr/bin/python

# enumerates boxes in aws accounts by envronment and role

import boto3
import argparse
import json
import sys

environment = ''
role = ''
profile_location = '/Users/jayharrison/.aws/credentials'

if len(sys.argv) == 4:
  account = str(sys.argv[1])
  environment = str(sys.argv[2])
  role = str(sys.argv[3])
elif len(sys.argv) == 3:
  account = str(sys.argv[1])
  if str(sys.argv[2]) in ['dev', 'qa', 'staging', 'perf', 'prod', 'beta']:
    environment = str(sys.argv[2])
  else:
    role = str(sys.argv[2])
elif len(sys.argv) == 2:
  account = str(sys.argv[1])
else:
  print "Usage 'boxes account (environment) (role)'"
  sys.exit(0)

#make sure profile is valid
profiles = open(profile_location)
if account in profiles.read():
  profile = account
else:
  print "Unrecognised profile"
  sys.exit(0)

boto3.setup_default_session(profile_name=profile)
client = boto3.client('ec2')

filter_list = []
if role:
  filter_list.append({ 'Name': 'tag:role', 'Values': [role]}) 

if environment:
  filter_list.append({ 'Name': 'tag:environment', 'Values': [environment]})

groups = client.describe_instances(
  Filters=filter_list
)

iplist = []
role_tag = ''
env_tag = ''

for instance in groups['Reservations']: 
  for i in instance['Instances']:
    if i['State']['Name'] == 'running':
      for t in i['Tags']:
        if t['Key'] == 'Environment' or t['Key'] == 'environment':
          env_tag = t['Value']
        if t['Key'] == 'Role' or t['Key'] == 'role':
          role_tag = t['Value']

      iplist.append([env_tag, role_tag, i['InstanceId'], i['PrivateIpAddress'], i['PublicDnsName']])

iplist.sort()

for row in iplist:
        print("{: <13} {: <20} {: <12} {: <14} {: <20}".format(*row))
