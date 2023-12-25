import json
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table = dynamodb.Table('Notifications')

    # Perform a scan operation (not efficient for large datasets)
    response = table.scan()

    notifications = response.get('Items', [])

    # Sort the notifications by timestamp (descending order) and get top 5
    sorted_notifications = sorted(notifications, key=lambda x: x['Timestamp'], reverse=True)[:5]

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(sorted_notifications)
    }
