"""
Lambda function to store today's shop in history.

This function snapshots all current shopping list items and stores them
in the ShopHistory table with timestamp, preserving all item details.
"""

import json
import boto3
import uuid
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
shopping_list_table = dynamodb.Table('ShoppingList')
shop_history_table = dynamodb.Table('ShoppingList-ShopHistory-Dev')


def lambda_handler(event, context):
    """
    Store today's shop to history.

    Creates a snapshot of all current items with all their details:
    - itemName, emoji, quantity, estimatedPrice, category
    - bought status
    - userId
    - Timestamp of when shop was stored

    Returns:
        dict: Response with status code and stored shop details
    """
    try:
        logger.info("Starting shop storage")

        # Scan all items from current shopping list
        response = shopping_list_table.scan()
        items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = shopping_list_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        logger.info(f"Found {len(items)} items to store")

        if len(items) == 0:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No items to store',
                    'message': 'Shopping list is empty'
                })
            }

        # Generate unique shop ID and timestamp
        shop_id = str(uuid.uuid4())
        shop_date = datetime.utcnow().isoformat() + 'Z'

        # Filter to only Gianluca and Nicole
        allowed_users = ['Gianluca', 'Nicole']
        filtered_items = [item for item in items if item.get('userId') in allowed_users]

        # Calculate totals
        total_items = len(filtered_items)
        total_price = sum((item.get('estimatedPrice', 0) * item.get('quantity', 1)) for item in filtered_items)

        # Create shop history record
        shop_record = {
            'shopId': shop_id,
            'shopDate': shop_date,
            'totalItems': total_items,
            'totalPrice': round(total_price, 2),
            'items': []
        }

        # Add each item with all details
        for item in filtered_items:
            shop_item = {
                'userId': item.get('userId', ''),
                'itemId': item.get('itemId', ''),
                'itemName': item.get('itemName', ''),
                'emoji': item.get('emoji', '🛒'),
                'quantity': item.get('quantity', 1),
                'estimatedPrice': item.get('estimatedPrice', 0.0),
                'category': item.get('category', 'Uncategorized'),
                'bought': item.get('bought', False)
            }
            shop_record['items'].append(shop_item)

        # Store in ShopHistory table
        shop_history_table.put_item(Item=shop_record)

        logger.info(f"Successfully stored shop {shop_id} with {total_items} items, total: £{total_price:.2f}")

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Shop stored successfully',
                'shop': {
                    'shopId': shop_id,
                    'shopDate': shop_date,
                    'totalItems': total_items,
                    'totalPrice': round(total_price, 2)
                }
            })
        }

    except Exception as e:
        logger.error(f"Error storing shop: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
