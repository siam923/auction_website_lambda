import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal, InvalidOperation
from datetime import datetime
import uuid
from boto3.dynamodb.conditions import Key

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    http_method = event.get('httpMethod')
    # Preflight request. Reply successfully:
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': ''
        }
    
    
    item_id = event.get('pathParameters', {}).get('id')
    
    if http_method == 'GET':
        # Extract 'itemId' from pathParameters for GET request
        return get_bids(item_id)
    elif http_method == 'POST':
        # Extract data from request body for POST request
        data = json.loads(event.get('body', '{}'))
        return create_bid(data, item_id)
    else:
        return {
            'statusCode': 405,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps('Method Not Allowed')
        }

def get_bids(item_id):
    try:
        table = dynamodb.Table('Bids')
        response = table.query(
            KeyConditionExpression=Key('ItemId').eq(item_id),
        )
        bids = response.get('Items', [])
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(bids, cls=DecimalEncoder)
        }
    except ClientError as e:
        # Log the error
        print(f"Error in get_bids: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps('Internal Server Error')
        }
def create_bid(data, item_id):
    try:
        table = dynamodb.Table('Bids')

        # Generate a new bidId and timestamp
        bid_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Extract userId, name, and price from the request data
        user_id = data.get('userId')
        name = data.get('name')

        # Validate and convert price to Decimal
        try:
            price = Decimal(str(data.get('price')))
        except (InvalidOperation, TypeError, ValueError):
            return {'statusCode': 400, 'body': json.dumps("Invalid price format")}

        # Create a new bid
        bid = {
            'BidId': bid_id,
            'ItemId': item_id,
            'userId': user_id,
            'name': name,
            'price': price,
            'time': timestamp
        }

        table.put_item(Item=bid)
        
        try:
            # Prepare the notification message
            message = f"New bid for product ID: {item_id}, Bid Amount: {price}"
            sns_response = sns_client.publish(
                TopicArn='arn:aws:sns:us-east-1:768218750071:AuctionBidNotifications',  # Replace with your SNS topic ARN
                Message=message,
                Subject='New Bid Notification'
            )
    
            # You can log the response or handle it as needed
            print(sns_response)
            
        except ClientError as e:
            print(f"Error in publishing to SNS: {e}")

        

        # Return successful response with CORS headers
        return {
            'statusCode': 201,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS, POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': json.dumps(bid, cls=DecimalEncoder)
        }

    except ClientError as e:
        # Log the error
        print(f"Error in create_bid: {e}")
        # Return error response with CORS headers
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS, POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': json.dumps(f"Error: {str(e)}")
        }

