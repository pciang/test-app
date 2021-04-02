#!/usr/bin/env python3

import sys
import functools

import requests
import boto3

class AutoConfigure:
  def __init__(self):
    self.ssm_client = boto3.client('ssm',
      region_name='ap-southeast-1',
    )
    self.ec2_client = boto3.client('ec2',
      region_name='ap-southeast-1',
    )

    self.zk_server_id_path = '/var/opt/zookeeper/myid'
    self.zk_config_path = '/opt/zookeeper/conf/zoo.cfg'

  @property
  @functools.lru_cache(maxsize=1)
  def instance_id(self) -> str:
    return requests.get('http://169.254.169.254/latest/meta-data/instance-id').text

  @property
  @functools.lru_cache(maxsize=1)
  def tags(self) -> dict:
    return dict((tag['Key'], tag['Value']) for tag in self.ec2_client.describe_instances(
        InstanceIds=[
          self.instance_id,
        ],
      )['Reservations'][0]['Instances'][0]['Tags']
    )

  def get_config_from_param_store(self) -> str:
    return self.ssm_client.get_parameter(Name='/zookeeper/config')['Parameter']['Value']

  def write_zk_server_id(self):
    with open(self.zk_server_id_path, mode='w') as zk_server_id_file:
      zk_server_id_file.write(self.tags['Zookeeper-ServerId'])

  def write_zk_config(self, zk_config: str):
    with open(self.zk_config_path, mode='w') as zk_config_file:
      zk_config_file.write(zk_config)

  def run(self) -> int:
    self.write_zk_server_id()
    zk_config = self.get_config_from_param_store()
    self.write_zk_config(zk_config)
    return 0

def main() -> int:
  return AutoConfigure().run()

if __name__ == '__main__':
  sys.exit(main())
