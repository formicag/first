"""
One-time script to backfill emojis for existing items in DynamoDB.
This script scans all items and uses AI to add emojis to items that don't have them.
"""

import json
import boto3
import logging
from createItem import process_item_with_ai

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ShoppingList')


def lambda_handler(event, context):
    """
    Scan all items in DynamoDB and add emojis to items that don't have them.
    """
    try:
        # Scan all items
        response = table.scan()
        items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        logger.info(f"Found {len(items)} total items")

        updated_count = 0
        skipped_count = 0

        for item in items:
            # Skip if item already has an emoji
            if 'emoji' in item and item['emoji']:
                logger.info(f"Item {item['itemId']} already has emoji: {item['emoji']}")
                skipped_count += 1
                continue

            item_name = item.get('itemName', '')
            user_id = item.get('userId', '')
            item_id = item.get('itemId', '')

            if not item_name:
                logger.warning(f"Item {item_id} has no itemName, skipping")
                skipped_count += 1
                continue

            logger.info(f"Processing item: {item_name} (user: {user_id}, id: {item_id})")

            # Use AI to get emoji (and revalidate name/category)
            ai_result = process_item_with_ai(
                item_name,
                custom_prompt='',
                context_items=[],
                use_uk_english=True,
                strict_categories=True
            )

            emoji = ai_result.get('emoji', '🛒')

            logger.info(f"AI assigned emoji: {emoji} for {item_name}")

            # Update item in DynamoDB
            table.update_item(
                Key={
                    'userId': user_id,
                    'itemId': item_id
                },
                UpdateExpression='SET emoji = :emoji',
                ExpressionAttributeValues={
                    ':emoji': emoji
                }
            )

            updated_count += 1
            logger.info(f"Updated item {item_id} with emoji {emoji}")

        logger.info(f"Backfill complete: {updated_count} items updated, {skipped_count} items skipped")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Backfill complete',
                'totalItems': len(items),
                'updatedCount': updated_count,
                'skippedCount': skipped_count
            })
        }

    except Exception as e:
        logger.error(f"Error during backfill: {str(e)}", exc_info=True)
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
