#!/usr/bin/env python3

import os
import sys
import configparser
import argparse

import boto3


def main() -> int:
  argparser = argparse.ArgumentParser()
  argparser.add_argument('--overwrite',
    help='Overwrites a specific profile',
    type=str,
  )
  argparser.add_argument('--source-profile',
    help='Select a specific profile to do MFA',
    type=str,
    default=None,
  )
  argparser.add_argument('--duration',
    help='How long the session lasts in seconds',
    type=int,
    default=3600,
  )
  argparser.add_argument('username', type=str)
  argparser.add_argument('token_code', type=str)
  argparser.add_argument('--credentials-path',
    help='Writes the temporary credential into this file',
    type=str,
    default='~/.aws/credentials',
  )
  args = argparser.parse_args()

  profile_name: str = args.source_profile

  my_session = boto3.session.Session(profile_name=profile_name)
  my_credentials = my_session.get_credentials()
  sts_client = boto3.client('sts',
    aws_access_key_id=my_credentials.access_key,
    aws_secret_access_key=my_credentials.secret_key,
  )

  username: str = args.username

  identity = sts_client.get_caller_identity()
  serial_number = 'arn:aws:iam::{:s}:mfa/{:s}'.format(
    identity['Account'],
    username,
  )

  token_code: str = args.token_code
  duration: int = args.duration

  response = sts_client.get_session_token(
    DurationSeconds=duration,
    SerialNumber=serial_number,
    TokenCode=token_code,
  )

  credentials_path: str = os.path.expanduser(args.credentials_path)

  config = configparser.ConfigParser()
  config.read(credentials_path)

  if args.overwrite is not None:
    overwritten_profile_name: str = args.overwrite
  elif profile_name is not None:
    overwritten_profile_name: str = f'{profile_name:s}-mfa'
  else:
    overwritten_profile_name = 'default-mfa'

  config[overwritten_profile_name] = {
      'aws_access_key_id': response['Credentials']['AccessKeyId'],
      'aws_secret_access_key': response['Credentials']['SecretAccessKey'],
      'aws_session_token': response['Credentials']['SessionToken'],
  }

  with open(credentials_path, 'w') as credentials_file:
    config.write(credentials_file)

  print('Authenticated successfully!')
  print(f'New credentials is written into this profile {overwritten_profile_name:s} in this file {credentials_path:s}.')

  return 0


if __name__ == '__main__':
  sys.exit(main())

