#!/usr/bin/env python3

import os
import sys
import stat
import subprocess
import re

import boto3

class AutoConfigure:
  FILE_EXT4_PATT = re.compile('^Linux rev 1.0 ext4')

  def __init__(self):
    self.ssm_client = boto3.client('ssm',
      region_name='ap-southeast-1',
    )

    self.config = self.get_config_from_param_store()
    self.next_serial_no = 0
    self.possible_devices = self.get_devices_from_param_store()

  def get_config_from_param_store(self) -> str:
    return self.ssm_client \
      .get_parameter(Name='/nfs-server/config')['Parameter']['Value']

  def get_devices_from_param_store(self) -> list:
    config: str = self.ssm_client \
      .get_parameter(Name='/nfs-server/devices')['Parameter']['Value']
    return config.strip().split('\n')

  def is_blk(self, device: str) -> bool:
    return stat.S_ISBLK(os.stat(device).st_mode)

  def is_ext4(self, device: str) -> bool:
    file_stdout = subprocess \
      .check_output(['file', '-s', '-b', device]) \
      .decode('utf-8')

    return self.FILE_EXT4_PATT.search(file_stdout) is not None

  def mkfs_ext4(self, device: str):
    subprocess.check_call(['mkfs.ext4', device])

  def mkdir_data(self) -> str:
    data_dir = f'/media/blk/{self.next_serial_no:02d}'
    subprocess.check_call(['mkdir', '-p', data_dir])
    subprocess.check_call(['chown', '-R', 'nobody:nogroup', data_dir])
    self.next_serial_no += 1
    return data_dir

  def mount_ext4(self, device: str, directory: str):
    subprocess.check_call(['mount', '-t', 'ext4', device, directory])

  def run(self) -> int:
    final_devices = []
    for device in self.possible_devices:
      if self.is_blk(device):
        if not self.is_ext4(device):
          self.mkfs_ext4(device)
        final_devices.append(device)

    data_dirs = []
    os.makedirs('/opt/nfs-server', exist_ok=True)
    mounted_dev_list_file = open('/opt/nfs-server/mounted', mode='w')
    for device in final_devices:
      data_dir = self.mkdir_data()
      self.mount_ext4(device, data_dir)
      mounted_dev_list_file.write(f'{device:s}\n')
      data_dirs.append(data_dir)

    with open('/etc/exports', mode='w') as exports:
      for data_dir in data_dirs:
        exports.write(f'{data_dir:s}  {self.config}\n')

    return 0

def main() -> int:
  return AutoConfigure().run()

if __name__ == '__main__':
  sys.exit(main())
