"""
Lambda function to retrieve shopping list items from DynamoDB.

This function queries items for a specific user with optional filtering
by bought status.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key
import logging
from decimal import Decimal
from store_layout import sort_items_by_store_layout

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ShoppingList')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON-serializable formats."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Retrieve shopping list items for all users.

    Expected input (JSON):
    {
        "boughtFilter": "all"  // optional: "true", "false", or "all" (default)
    }

    Returns:
        dict: Response with status code and list of items
    """
    try:
        query_params = event.get('queryStringParameters', {}) or {}

        # Get boughtFilter from query string (defaults to 'all')
        bought_filter = query_params.get('bought', 'all').lower()

        # Validate boughtFilter value
        if bought_filter not in ['all', 'true', 'false']:
            logger.error(f"Invalid boughtFilter value: {bought_filter}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'boughtFilter must be "all", "true", or "false"'
                })
            }

        # Scan all items from all users
        logger.info(f"Scanning all items for all users, filter: {bought_filter}")

        response = table.scan()

        items = response.get('Items', [])

        # Apply bought filter if specified
        if bought_filter == 'true':
            items = [item for item in items if item.get('bought') is True]
        elif bought_filter == 'false':
            items = [item for item in items if item.get('bought') is False]

        # Sort by store layout (entrance to back) for better shopping experience
        items = sort_items_by_store_layout(items)

        logger.info(f"Found {len(items)} items from all users")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'count': len(items),
                'items': items
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error(f"Error retrieving items: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
