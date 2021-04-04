#!/usr/bin/env python3

import os
import sys
import subprocess

def umount_ext4(device: str):
  subprocess \
    .check_call(['umount', '-t', 'ext4', device])

def main() -> int:
  if not os.path.isfile('/opt/nfs-server/mounted'):
    return 0

  with open('/opt/nfs-server/mounted', mode='r') as devices:
    for line in devices:
      device = line.strip()
      umount_ext4(device)

  os.remove('/opt/nfs-server/mounted')
  return 0

if __name__ == '__main__':
  sys.exit(main())
