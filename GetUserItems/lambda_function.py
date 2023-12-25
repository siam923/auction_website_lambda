import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from datetime import datetime
from decimal import Decimal


# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')

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
    
    if http_method == 'GET':
        # Extract 'userId' from queryParameters for GET request
        query_parameters = event.get('queryStringParameters', {})
        user_id = query_parameters.get('userId')
        return check_bid_status(user_id)
    else:
        return {
            'statusCode': 405,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps('Method Not Allowed')
        }
        
    
        
def check_bid_status(user_id):
    try:
        bids_table = dynamodb.Table('Bids')
        items_table = dynamodb.Table('AuctionItems')

        # Get all bids for the user
        response = bids_table.query(
            IndexName='userId-index',
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        user_bids = response.get('Items', [])
        result = []

        # Get the current time
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        item_details_cache = {}
        processed_item_ids = set()  # Set to track processed item IDs

        # Check the status of each bid
        for bid in user_bids:
            item_id = bid['ItemId']
            bid_id = bid['BidId']

            # Skip if the item_id is already processed
            if item_id in processed_item_ids:
                continue

            processed_item_ids.add(item_id)  # Add item_id to the set

            if item_id not in item_details_cache:
                item_response = items_table.get_item(Key={'ItemId': item_id})
                item_details_cache[item_id] = item_response.get('Item', {})
           
            item = item_details_cache[item_id]
            auction_end_time = item.get('auctionEndTime')

            # Retrieve the highest bid information
            highest_bid_response = bids_table.query(
                IndexName='ItemId-price-index',
                KeyConditionExpression=Key('ItemId').eq(item_id),
                ScanIndexForward=False,
                Limit=1
            )

            highest_bid = highest_bid_response.get('Items', [])[0]
            highest_bid_user_id = highest_bid['userId']
            highest_bid_username = highest_bid['name']
            highest_bid_price = highest_bid['price']

            if current_time >= auction_end_time:
                status = 'win' if bid_id == highest_bid['BidId'] else 'lost'
            else:
                status = 'ongoing'

            result.append({
                'itemId': item_id,
                'status': status,
                'bidId': bid_id,
                'user_id': highest_bid_user_id,
                'user_name': highest_bid_username,
                'price': highest_bid_price
            })

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result, cls=DecimalEncoder)
        }
    except ClientError as e:
        print(f"Error in check_bid_status: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps('Internal Server Error')
        }
