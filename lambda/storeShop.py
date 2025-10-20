"""
Lambda function to store today's shop in history.

WORKFLOW:
1. Save only TICKED items (bought=True) to shop history
2. UNTICK items (set bought=False) - keep them on the list for next shop
3. Items remain on shopping list for future shops

This saves a record of what was bought while keeping items for next time.
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
    Store today's shop to history (only ticked items).

    Workflow:
    1. Find all items with bought=True (ticked)
    2. Save these to shop history
    3. Untick these items (set bought=False) - keep them on list for next shop

    Returns:
        dict: Response with status code and stored shop details
    """
    try:
        logger.info("Starting shop storage with new workflow")

        # Scan all items from current shopping list
        response = shopping_list_table.scan()
        items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = shopping_list_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        logger.info(f"Found {len(items)} total items")

        # Filter to only Gianluca and Nicole
        allowed_users = ['Gianluca', 'Nicole']
        user_items = [item for item in items if item.get('userId') in allowed_users]

        # Separate ticked (bought) from non-ticked items
        ticked_items = [item for item in user_items if item.get('bought') is True]
        non_ticked_items = [item for item in user_items if item.get('bought') is not True]

        logger.info(f"Ticked items (to save to history): {len(ticked_items)}")
        logger.info(f"Non-ticked items (to keep): {len(non_ticked_items)}")

        if len(ticked_items) == 0:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No ticked items to save',
                    'message': 'Please tick items you purchased before saving your shop'
                })
            }

        # Generate unique shop ID and timestamp
        shop_id = str(uuid.uuid4())
        shop_date_full = datetime.utcnow()
        shop_date = shop_date_full.isoformat() + 'Z'
        today_date = shop_date_full.strftime('%Y-%m-%d')  # Date only for querying

        # Delete previous shops from today (optional - keeps only one shop per day)
        logger.info(f"Checking for previous shops from today: {today_date}")
        try:
            scan_response = shop_history_table.scan()
            today_shops = scan_response.get('Items', [])

            while 'LastEvaluatedKey' in scan_response:
                scan_response = shop_history_table.scan(ExclusiveStartKey=scan_response['LastEvaluatedKey'])
                today_shops.extend(scan_response.get('Items', []))

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

        # Calculate totals for ticked items only
        total_items = len(ticked_items)
        total_price = Decimal('0')
        for item in ticked_items:
            price = item.get('estimatedPrice', 0)
            if isinstance(price, Decimal):
                total_price += price * item.get('quantity', 1)
            else:
                total_price += Decimal(str(price)) * item.get('quantity', 1)

        # Create shop history record (only ticked items)
        shop_record = {
            'shopId': shop_id,
            'shopDate': shop_date,
            'totalItems': total_items,
            'totalPrice': total_price,
            'items': []
        }

        # Add each ticked item to shop history
        for item in ticked_items:
            price = item.get('estimatedPrice', 0)
            if not isinstance(price, Decimal):
                price = Decimal(str(price)) if price else Decimal('0')

            shop_item = {
                'userId': item.get('userId', ''),
                'itemId': item.get('itemId', ''),
                'itemName': item.get('itemName', ''),
                'quantity': item.get('quantity', 1),
                'estimatedPrice': price,
                'category': item.get('category', 'Uncategorized'),
                'bought': True  # All items in history were bought
            }
            shop_record['items'].append(shop_item)

        # Store in ShopHistory table
        shop_history_table.put_item(Item=shop_record)
        logger.info(f"Shop {shop_id} saved to history with {total_items} items, £{total_price:.2f}")

        # UNTICK items (set bought=False) - keep them on the list for next shop
        unticked_count = 0
        for item in ticked_items:
            try:
                shopping_list_table.update_item(
                    Key={
                        'userId': item['userId'],
                        'itemId': item['itemId']
                    },
                    UpdateExpression='SET bought = :false',
                    ExpressionAttributeValues={
                        ':false': False
                    }
                )
                unticked_count += 1
            except Exception as e:
                logger.error(f"Error unticking item {item.get('itemId')}: {str(e)}")

        logger.info(f"Unticked {unticked_count} items - kept on list for next shop")
        logger.info(f"Total items on list: {len(user_items)}")

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Shop saved successfully',
                'shop': {
                    'shopId': shop_id,
                    'shopDate': shop_date,
                    'totalItems': total_items,
                    'totalPrice': float(total_price)
                },
                'itemsUnticked': unticked_count,
                'totalItemsOnList': len(user_items)
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
