import json
import boto3
from datetime import datetime
import uuid

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table = dynamodb.Table('Notifications')

    for record in event['Records']:
        # Extract message from the SNS notification
        message = record['Sns']['Message']

        # Generate a unique ID and current timestamp for the notification
        notification_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Store the notification in DynamoDB
        table.put_item(Item={
            'NotificationId': notification_id,
            'Timestamp': timestamp,
            'Message': message
        })

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed SNS message.')
    }
