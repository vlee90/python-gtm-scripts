"""Access and manage a Google Tag Manager account."""

import argparse
import sys

import httplib2

from apiclient.discovery import build
from oauth2client import client
from oauth2client import file
from oauth2client import tools

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

def FindContainerId(service, account_id, container_name):
  """Find the greetings container ID.

  Args:
    service: the Tag Manager service object.
    account_id: the ID of the Tag Manager account from which to retrieve the
      Greetings container.
    container_name: the name of the GTM container.

  Returns:
    The dictionary that represents the greetings container if it exists, or None
    if it does not.
  """
  # Query the Tag Manager API to list all containers for the given account.
  container_wrapper = service.accounts().containers().list(
      accountId=account_id).execute()

  # Find and return the Greetings container if it exists.
  for container in container_wrapper['containers']:
    if container['name'] == container_name:
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

# TAGS
def CallAllTags(service, account_id, container_id):
  tags = service.accounts().containers().tags().list(
    accountId=account_id,
    containerId=container_id
    ).execute()
  return tags

def ReturnTagsOfTagType(tags, type):
  universal_tags = []
  for tag in tags['tags']:
    if tag['type'] == type:
      universal_tags.append(tag)
    pass

  return universal_tags

def DeleteTagWithTagId(service, account_id, container_id, tag_id):
  try:
    service.accounts().containers().tags().delete(
      accountId=account_id,
      containerId=container_id,
      tagId=tag_id).execute()
    print 'Deleted tagId: {}'.format(tag_id)

  except TypeError, error:
    print 'There was an error in building the query: %s' %error

  # except HttpError, error:
    # print ('There was an API error: %s :%s' % (error.resp.status, error.resp.reason))

def DeleteAllTagsThatHaveNoTriggers(service, account_id, container_id):
  tags = ReturnAllTags(service, account_id, container_id)
  tags = tags['tags']
  for tag in tags:
    if 'firingTriggerId' in tag:

      pass
    elif 'teardownTag' in tag:

      pas
    else:
      print tag['tagId']
      DeleteTagWithTagId(service,account_id,container_id,tag['tagId'])
      pass  

# TRIGGERS
def CallAllTriggers(service, account_id, container_id):
  triggers = service.accounts().containers().triggers().list(
    accountId=account_id,
    containerId=container_id).execute()
  return triggers

def DeleteTriggerWithTriggerId(service, account_id, container_id, trigger_id):
  try:
    service.accounts().containers().triggers().delete(
      accountId=account_id,
      containerId=container_id,
      triggerId=trigger_id).execute()
    print 'Deleted triggerId: {}'.format(trigger_id)

  except TypeError, error:
    print 'There was an error in building the query: %s' %error

def DeleteAllTriggersThatHaveNoTag(service, account_id,container_id):
  triggers = CallAllTriggers(service, account_id, container_id)
  triggers = triggers['triggers']
  triggerObjects = []
  blankTriggerIds = []

  tags = CallAllTags(service, account_id, container_id)
  tags = tags['tags']
  tagFiringTriggersIds = []

  # Gets all Trigger IDs in container
  for trigger in triggers:
    trigger_id = trigger['triggerId']
    triggerObjects.append(trigger_id)

  # Gets all Triggers IDs that fire a Tag
  for tag in tags:
    if 'firingTriggerId' in tag:
      for triggerId in tag['firingTriggerId']:
        tagFiringTriggersIds.append(triggerId)
    if 'blockingTriggerId' in tag:
      for triggerId in tag['blockingTriggerId']:
        tagFiringTriggersIds.append(triggerId)
    if 'firingRuleId' in tag:
      for triggerId in tag['firingRuleId']:
        tagFiringTriggersIds.append(triggerId)
    if 'blockingRuleId' in tag:
      for triggerId in tag['blockingRuleId']:
        tagFiringTriggersIds.append(triggerId)

  tagFiringTriggersIds = set(tagFiringTriggersIds)

  # Test array
  firingTriggerId = []

  # Get all Trigger IDs that are not attached to a Tag
  for triggerId in triggerObjects:
    if triggerId in tagFiringTriggersIds:
      firingTriggerId.append(triggerId)
    else:
      blankTriggerIds.append(triggerId)

  for trigger_id in blankTriggerIds:
    DeleteTriggerWithTriggerId(service, account_id, container_id, trigger_id)

# VARIABLES
def CallAllVariables(service, account_id, container_id):
    variables = service.accounts().containers().variables().list(
    accountId=account_id,
    containerId=container_id).execute() 
    return variables

def CreateVariable(service, account_id, container_id, name, type):
  try:
    body = {
      'name' : name,
      'type' : type,
      'parameter' : [
        {
          'type' : 'integer',
          'key' : 'dataLayerVersion',
          'value' : '2'
        },
        {
          'type' : 'template',
          'key' : 'name',
          'value' : 'testVariable'
        }
        ]
    }
    service.accounts().containers().variables().create(
    accountId=account_id,
    containerId=container_id,
    body=body).execute()
    print 'Created variable name: {}'.format(name)
  except TypeError, error:
    print 'There was an error in building the query: %s' %error

  # except HttpError, error:
    # print ('There was an API error: %s :%s' % (error.resp.status, error.resp.reason))

def DeleteVariableWithVariableID(service, account_id, container_id, variable_id):
  try:
    service.accounts().containers().variables().delete(
    accountId=account_id,
    containerId=container_id,
    variableId=variable_id).execute()
    print 'Deleted variableId: {}'.format(variable_id)
  except TypeError, error:
    print 'There was an error in building the query: %s' %error

  except HttpError, error:
    print ('There was an API error: %s :%s' % (error.resp.status, error.resp.reason))

def DeleteVariablesThatAreUnused(service, account_id, container_id):
  triggers = CallAllTriggers(service, account_id, container_id)
  triggers = triggers['triggers']

  variables = CallAllVariables(service, account_id, container_id)
  variables = variables['variables']  

  # Total List of Variable IDs in the GTM Container 
  variableObject = []
  for variable in variables:
    variableId = variable['variableId']  
    variableName = variable['name']
    variableObject.append(
      {
        'name': variableName,
        'variableId': variableId
      })

  # All Custom JavaScript Variables
  customJavaScriptVariables = []
  for variable in variables:
    if variable['type'] == 'jsm':
      customJavaScriptVariables.append(variable)

  # All LookUp Variables
  lookupVariable = []
  for variable in variables:
    if variable['type'] == 'smm':
      lookupVariable.append(variable)

  # Total List of Tags in the GTM Container
  tags = CallAllTags(service, account_id, container_id)
  tags = tags['tags']

  usedVariables = []
  for variable in variableObject:
    name = variable['name']
    seq = ('{{', name, '}}')
    gtmVariableName =  ''.join(seq)
    # Stringify Tags
    for tag in tags:
      tagString = str(tag)
      isValuePresent = tagString.find(gtmVariableName)
      if isValuePresent != -1:
        usedVariables.append(variable['variableId'])
        print 'Variable ID: {} is present'.format(variable['variableId'])
    for jsmVariable in customJavaScriptVariables:
      jsmVariableString = str(jsmVariable)
      isValuePresent = jsmVariableString.find(gtmVariableName)
      if isValuePresent != -1:
       usedVariables.append(variable['variableId'])
       print 'Variable ID: {} is present'.format(variable['variableId'])
    for smmVariable in lookupVariable:
      smmVariableString = str(smmVariable)
      isValuePresent = smmVariableString.find(gtmVariableName)
      if isValuePresent != -1:
        usedVariables.append(variable['variableId'])
        print 'Variable ID: {} is present'.format(variable['variableId'])
    for trigger in triggers:
      triggerString = str(trigger)
      isValuePresent = triggerString.find(gtmVariableName)
      if isValuePresent != -1:
        usedVariables.append(variable['variableId'])
        print 'Variable ID: {} is present'.format(variable['variableId'])
  
  usedVariables = set(usedVariables)
  unusedVariableIds = []

  for variable in variableObject:
    variableId = variable['variableId']
    if variableId in usedVariables:
      print 'VariableId: {} is Used'.format(variableId)
      pass
    else:
      print 'VariableId: {} is Unused'.format(variableId)
      unusedVariableIds.append(variableId)

  print 'Unused:'
  print unusedVariableIds
  print 'Used:'
  print usedVariables

  for variableId in unusedVariableIds:
    print variableId
    DeleteVariableWithVariableID(service, account_id, container_id, variableId)

def CreateDataLayerVariable(service, accountId, containerId, name, dLVariableName, defaultValue):
  parameter = [ParameterKeyName(name)]
  if defaultValue != None:
    parameter.append(ParameterKeyDefaultValue(defaultValue))
    parameter.append(ParameterKeySetDefaultValue('true'))

  service.accounts().containers().variables().create(
    accountId=accountId,
    containerId=containerId,
    body={
      'name' : name,
      'type' : 'v',
      'parameter' : parameter
    }).execute()

def ParameterKeyName(name):
  return {'type': 'template','key': 'name','value': name}

def ParameterKeySetDefaultValue(isDefaultValue):
  return {'type': 'boolean','key': 'setDefaultValue','value': isDefaultValue}

def ParameterKeyDefaultValue(defaultValue):
  return {'type': 'template','key': 'defaultValue','value': defaultValue}

def CreateConstantVariable(service, accountId, containerId, name, value):
  parameter = [ParameterKeyValue(value)]

  service.accounts().containers().variables().create(
    accountId=accountId,
    containerId=containerId,
    body={
      'name' : name,
      'type' : 'c',
      'parameter' : parameter
    }).execute()

def ParameterKeyValue(value):
  return {'type': 'template','key': 'value', 'value': value}

def main(argv):
  # Get tag manager account ID from command line.
  assert len(argv) == 3 and 'usage: main.py <account_id> <container_name>'
  account_id = str(argv[1])
  container_name = str(argv[2])

  # Define the auth scopes to request.
  scope = ['https://www.googleapis.com/auth/tagmanager.edit.containers']

  # Authenticate and construct service.
  service = GetService('tagmanager', 'v1', scope, 'client_secrets.json')

  # Find the greetings container.
  container_id = FindContainerId(service, account_id, container_name)

  CreateConstantVariable(service,account_id,container_id,'testconstant', 'tet')

if __name__ == "__main__":
  main(sys.argv)       