#!/usr/bin/env python3

import sys
import functools

import boto3
import requests
import jinja2

class AutoConfigure:
  def __init__(self):
    self.ec2_client = boto3.client('ec2', region_name=self.region)

  @property
  @functools.lru_cache(maxsize=1)
  def region(self) -> str:
    return requests.get(
      'http://169.254.169.254/latest/meta-data/placement/region',).text

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

  @property
  @functools.lru_cache(maxsize=1)
  def cluster_name(self) -> str:
    return self.tags['Elasticsearch-Cluster']

  @property
  @functools.lru_cache(maxsize=1)
  def node_name(self) -> str:
    return self.tags['Elasticsearch-Node']

  def run(self) -> int:
    with open('/opt/elasticsearch/config/elasticsearch.yml', mode='r') as template_file:
      config_template = jinja2.Template(template_file.read())

    with open('/opt/elasticsearch/config/elasticsearch.yml', mode='w') as config_file:
      config_file.write(
        config_template.render(
          cluster_name=self.cluster_name,
          node_name=self.node_name,
          network_host=f'{self.node_name}.internal',
          seed_hostname='elasticsearch.internal',
        ),
      )

    return 0

def main() -> int:
  return AutoConfigure().run()

if __name__ == '__main__':
  sys.exit(main())
