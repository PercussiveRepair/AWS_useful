#! /usr/bin/python

# gets instance events from mulitple accounts/regions and posts to slack

import boto3
from slackclient import SlackClient
from tabulate import tabulate

token = '<slack token>'
creds = open('<creds location>', 'r')
regions = ['eu-west-1', 'us-east-1']
filters = [{ 'Name': 'event.code', 'Values': [ 'instance-reboot','system-reboot','system-maintenance','instance-retirement','instance-stop']}]
instanceevents = []

# get instance maintenance data
try:
  for line in creds:
    if line.startswith('['):
      profile=line[1:-2]
      print profile
      for region in regions:
        boto3.setup_default_session(profile_name=profile, region_name=region)
        client = boto3.client('ec2')
        for status in client.describe_instance_status(Filters=filters)['InstanceStatuses']:
          instance = client.describe_instances(InstanceIds=[status['InstanceId']])
          instancename = 'Undefined'
          instancerole = 'Undefined'
          instanceproduct = 'Undefined'
          if 'Tags' in instance['Reservations'][0]['Instances'][0]:
            for tag in instance['Reservations'][0]['Instances'][0]['Tags']:
              if tag['Key'] == 'Name':
                instancename = tag['Value']
              elif tag['Key'] == 'role':
                instancerole = tag['Value']
              elif tag['Key'] == 'product':
                instanceproduct = tag['Value']
          instanceinfo = { 'Account': profile, 'InstanceId': status['InstanceId'], 'Action': status['Events'][0]['Code'], 'Status': status['Events'][0]['Description'], 'Name': instancename, 'Role': instancerole, 'Product': instanceproduct, 'Region/AZ': status['AvailabilityZone'], 'DueDate': status['Events'][0]['NotBefore']}
          instanceevents.append(instanceinfo)
except Exception,e: 
  print str(e)
  pass
  
# assemble slack message
table = tabulate(instanceevents, headers='keys') 
message = '```' + table + '```'

sc = SlackClient(token)
print sc.api_call(
        "chat.postMessage", channel="<slack channel>", text=message,
        username='AWS Instance Events', icon_emoji=':bomb:'
)
