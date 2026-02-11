import json
import boto3
import os

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    action = event.get('action', 'stop')
    environment = os.environ.get('ENVIRONMENT', 'stage')
    
    # Find instances with the environment tag and AutoShutdown=true
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Environment', 'Values': [environment]},
            {'Name': 'tag:AutoShutdown', 'Values': ['true']},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
    )
    
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    
    if not instance_ids:
        return {
            'statusCode': 200,
            'body': json.dumps(f'No instances found for environment: {environment}')
        }
    
    if action == 'stop':
        ec2.stop_instances(InstanceIds=instance_ids)
        message = f'Stopped instances: {instance_ids}'
    elif action == 'start':
        ec2.start_instances(InstanceIds=instance_ids)
        message = f'Started instances: {instance_ids}'
    else:
        return {
            'statusCode': 400,
            'body': json.dumps(f'Invalid action: {action}')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
