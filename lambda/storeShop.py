"""
Lambda function to store today's shop in history.

This function snapshots all current shopping list items and stores them
in the ShopHistory table with timestamp, preserving all item details.
"""

import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal
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
        shop_date_full = datetime.utcnow()
        shop_date = shop_date_full.isoformat() + 'Z'
        today_date = shop_date_full.strftime('%Y-%m-%d')  # Date only for querying

        # Delete previous shops from today
        logger.info(f"Checking for previous shops from today: {today_date}")
        try:
            # Query all shops from today
            scan_response = shop_history_table.scan()
            today_shops = scan_response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in scan_response:
                scan_response = shop_history_table.scan(ExclusiveStartKey=scan_response['LastEvaluatedKey'])
                today_shops.extend(scan_response.get('Items', []))

            # Filter to only shops from today
            for shop in today_shops:
                shop_date_str = shop.get('shopDate', '')
                if shop_date_str.startswith(today_date):
                    logger.info(f"Deleting previous shop from today: {shop.get('shopId')}")
                    shop_history_table.delete_item(
                        Key={
                            'shopId': shop.get('shopId'),
                            'shopDate': shop_date_str
                        }
                    )
        except Exception as e:
            logger.warning(f"Error deleting previous shops: {str(e)}")
            # Continue even if deletion fails

        # Filter to only Gianluca and Nicole
        allowed_users = ['Gianluca', 'Nicole']
        filtered_items = [item for item in items if item.get('userId') in allowed_users]

        # Calculate totals - handle both Decimal and float types
        total_items = len(filtered_items)
        total_price = Decimal('0')
        for item in filtered_items:
            price = item.get('estimatedPrice', 0)
            if isinstance(price, Decimal):
                total_price += price * item.get('quantity', 1)
            else:
                total_price += Decimal(str(price)) * item.get('quantity', 1)

        # Create shop history record
        shop_record = {
            'shopId': shop_id,
            'shopDate': shop_date,
            'totalItems': total_items,
            'totalPrice': total_price,
            'items': []
        }

        # Add each item with all details
        for item in filtered_items:
            price = item.get('estimatedPrice', 0)
            # Convert to Decimal if not already
            if not isinstance(price, Decimal):
                price = Decimal(str(price)) if price else Decimal('0')

            shop_item = {
                'userId': item.get('userId', ''),
                'itemId': item.get('itemId', ''),
                'itemName': item.get('itemName', ''),
                'emoji': item.get('emoji', '🛒'),
                'quantity': item.get('quantity', 1),
                'estimatedPrice': price,
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
                    'totalPrice': float(total_price)
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
