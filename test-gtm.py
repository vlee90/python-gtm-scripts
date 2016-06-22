"""Access and manage a Google Tag Manager account."""

import argparse
import sys

import httplib2

from apiclient.discovery import build
from oauth2client import client
from oauth2client import file
from oauth2client import tools

import trigger

def GetService(api_name, api_version, scope, client_secrets_path):
  """Get a service that communicates to a Google API.

  Args:
    api_name: string The name of the api to connect to.
    api_version: string The api version to connect to.
    scope: A list of strings representing the auth scopes to authorize for the
      connection.
    client_secrets_path: string A path to a valid client secrets file.

  Returns:
    A service that is connected to the specified API.
  """
  # Parser command-line arguments.
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      parents=[tools.argparser])
  flags = parser.parse_args([])

  # Set up a Flow object to be used if we need to authenticate.
  flow = client.flow_from_clientsecrets(
      client_secrets_path, scope=scope,
      message=tools.message_if_missing(client_secrets_path))

  # Prepare credentials, and authorize HTTP object with them.
  # If the credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # credentials will get written back to a file.
  storage = file.Storage(api_name + '.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, flags)
  http = credentials.authorize(http=httplib2.Http())

  # Build the service object.
  service = build(api_name, api_version, http=http)

  return service

def FindGreetingsContainerId(service, account_id):
  """Find the greetings container ID.

  Args:
    service: the Tag Manager service object.
    account_id: the ID of the Tag Manager account from which to retrieve the
      Greetings container.

  Returns:
    The dictionary that represents the greetings container if it exists, or None
    if it does not.
  """
  # Query the Tag Manager API to list all containers for the given account.
  container_wrapper = service.accounts().containers().list(
      accountId=account_id).execute()

  # Find and return the Greetings container if it exists.
  for container in container_wrapper['containers']:
    if container['name'] == 'CONTAINER NAME':
      return container['containerId']
  return None

def DefineFieldToSetWithUserID(tag, user_id_value):
  user_id_object = {
    'type':'list',
    'key':'fieldsToSet',
    'list':[
      {
        'type':'map',
        'map':[
          {
            'type':'template',
            'key':'fieldName',
            'value':'&uid'
          },
          {
            'type':'template',
            'key':'value',
            'value':user_id_value
          }
        ]
      }
    ]
  }
  tag['parameter'].append(user_id_object)
  return tag

def AddFieldToSetWithUserID(tag, user_id_value):
  user_id_object = {
    'type':'map',
    'map':[
      {
        'type':'template',
        'key':'fieldName',
        'value':'&uid'
      },
      {
        'type':'template',
        'key':'value',
        'value':user_id_value
      }
    ]
  }
  for parameter in tag['parameter']:
    if parameter['key'] == 'fieldsToSet':
      parameter['list'].append(user_id_object)
      pass
    pass
  return tag



def UpdateTagWithUserID(service, account_id, container_id, tag):
  user_id_present = False
  field_to_set_present = False
  for parameter in tag['parameter']:
    if parameter['key'] == 'fieldsToSet':
      field_to_set_present = True
      for maps in parameter['list']:
        for field in maps['map']:
          if field['value'] == '&uid':
            user_id_present = True
            break
            pass
          pass
        pass
      pass
    pass
  if user_id_present == False and field_to_set_present == False:
    print 'Will Add Field to Set AND User ID'
    tag = DefineFieldToSetWithUserID(tag, '{{user id}}')
    tag_id = tag['tagId']
    # Update the Tag.
    response = service.accounts().containers().tags().update(
      accountId=account_id,
      containerId=container_id,
      tagId=tag_id,
      body=tag).execute()
    pass

  if user_id_present == False and field_to_set_present == True:
    print 'Will Add User ID to Field to Set'
    tag = AddFieldToSetWithUserID(tag,'{{user id}}')
    tag_id = tag['tagId']
      # Update the Tag.
    response = service.accounts().containers().tags().update(
        accountId=account_id,
        containerId=container_id,
        tagId=tag_id,
        body=tag).execute()
    pass

  if user_id_present == True:
    print 'Tag already has User ID'
    pass

def ReturnAllUniversalAnalyticsTags(service, account_id, container_id):
  universal_tags = []
  tags = service.accounts().containers().tags().list(
    accountId=account_id,
    containerId=container_id).execute()
  for tag in tags['tags']:
    if tag['type'] == 'ua':
      universal_tags.append(tag)
    pass

  return universal_tags


def main(argv):
  # Get tag manager account ID from command line.
  assert len(argv) == 2 and 'usage: test-gtm.py <account_id>'
  account_id = str(argv[1])

  # Define the auth scopes to request.
  scope = ['https://www.googleapis.com/auth/tagmanager.edit.containers']

  # Authenticate and construct service.
  service = GetService('tagmanager', 'v1', scope, 'client_secrets.json')

  # Find the greetings container.
  container_id = FindGreetingsContainerId(service, account_id)

  # Returns all UA tags
  # tags = ReturnAllUniversalAnalyticsTags(service,account_id,container_id)

  # config_count = 0
  # for tag in tags:
  #   tag_id = tag['tagId']
  #   UpdateTagWithUserID(service, account_id, container_id, tag)    
  #   config_count = config_count + 1
  #   print 'Configurations Complete: {}'.format(config_count)


  # print "User ID Configuration Complete"

  printThis('hi')

if __name__ == "__main__":
  main(sys.argv)       