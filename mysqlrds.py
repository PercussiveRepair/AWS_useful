#!/usr/bin/env python
import sys, os
import boto.rds
from pprint import pprint

def print_usage():
    print """
    ego-mysqlrds launch  <id> <db_name>
    ego-mysqlrds status  <id>
    """

class RDS(object):

    def __init__(self,config):
        self.config = config
        self.api = boto.rds.connect_to_region("eu-west-1")

    def do_check(self):
        db = self.api.get_all_dbinstances(self.config.get('id'))
        for dbi in db:
          pprint(dbi)



class MySQLRDS(RDS):

    def __init__(self, config):
        RDS.__init__(self, config)
        self.tmpl = "try\nmysql -h %(ipaddress)s -u username -p mysql"

    def do_launch(self):
        ret = self.api.create_dbinstance(
            self.config.get('id'),
            self.config.get('size', 10), #allocated_storage, in GB [5-1024]
            self.config.get('instance_class','db.m1.large'), #instance_class
            self.config.get('master_username','root'),
            self.config.get('master_password','password'),
            port=3306,
            engine='mysql',
            db_name=self.config.get('db_name'),
            param_group='ego-live',
            security_groups=['default','ego-live-db'],
            availability_zone='eu-west-1c',
            preferred_maintenance_window='Sun:05:00-Sun:06:00',
            backup_retention_period=30,
            preferred_backup_window='03:00-04:00',
            multi_az=False,
            engine_version='5.5.31',
            auto_minor_version_upgrade=True
        )
        print("Launching. Go here to check progress: https://console.aws.amazon.com/rds/home?region=eu-west-1#dbinstances")
        return ret

def main():
    import optparse
    parser = optparse.OptionParser()
    opts, args = parser.parse_args()

    if len(args) < 2:
        print_usage()
        sys.exit()

#    cmd, dbid, db_name_opt = args[0], args[1], args[2]

    if   args[0] == 'launch':
      cmd, dbid, db_name_opt = args[0], args[1], args[2]
      rds = MySQLRDS({"id":dbid,"db_name":db_name_opt})
      rds.do_launch()
    elif args[0] == 'status':
      cmd, dbid = args[0], args[1]
      rds = MySQLRDS({"id":dbid})
      rds.do_check()
    else:
      print_usage()

if __name__ == '__main__':
    main()
