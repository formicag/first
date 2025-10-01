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
    Retrieve shopping list items for a user.

    Expected input (JSON):
    {
        "userId": "Gianluca",
        "boughtFilter": "all"  // optional: "true", "false", or "all" (default)
    }

    Returns:
        dict: Response with status code and list of items
    """
    try:
        # Extract userId from path parameters
        path_params = event.get('pathParameters', {})
        query_params = event.get('queryStringParameters', {}) or {}

        # Get userId from path
        user_id = path_params.get('userId')

        if not user_id:
            logger.error("Missing required field: userId")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required field: userId'
                })
            }

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

        # Query items for the user
        logger.info(f"Querying items for user: {user_id}, filter: {bought_filter}")

        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )

        items = response.get('Items', [])

        # Apply bought filter if specified
        if bought_filter == 'true':
            items = [item for item in items if item.get('bought') is True]
        elif bought_filter == 'false':
            items = [item for item in items if item.get('bought') is False]

        # Sort by addedDate (most recent first)
        items.sort(key=lambda x: x.get('addedDate', ''), reverse=True)

        logger.info(f"Found {len(items)} items for user {user_id}")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'userId': user_id,
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
