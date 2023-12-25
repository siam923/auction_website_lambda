import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        path_parameters = event.get('pathParameters', {})
        table = dynamodb.Table('AuctionItems')

        if path_parameters:
            item_id = event.get('pathParameters', {}).get('id')
            # Fetch a specific item if ID is provided
            response = table.get_item(
                Key={'ItemId': item_id},
            )
            item = response.get('Item')
            if item is not None:
                return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(item, cls=DecimalEncoder)}
            else:
                return {'statusCode': 404, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(f'Item with ID {item_id} not found')}
        else:
            # Fetch all items if ID is not provided
            response = table.scan()
            items = response.get('Items', [])
            return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(items, cls=DecimalEncoder)}
    except ClientError as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(f'Internal Server Error: {str(e)}')}
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(f'Error: {str(e)}')}

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)
