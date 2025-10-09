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
from cognito_helper import get_user_id_from_claims

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
    Retrieve shopping list items for all users (Cognito bypass mode).

    Expected input (JSON):
    {
        "boughtFilter": "all"  // optional: "true", "false", or "all" (default)
    }

    Returns:
        dict: Response with status code and list of items
    """
    try:
        # BYPASS MODE: Get all items from all users
        # Uncomment the code below to re-enable Cognito user filtering
        """
        # Extract userId from Cognito authorizer claims
        user_id = get_user_id_from_claims(event)
        query_params = event.get('queryStringParameters', {}) or {}

        if not user_id:
            logger.error("Unable to extract userId from token claims")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Unauthorized: Invalid token'
                })
            }
        """

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

        # BYPASS MODE: Scan all items (not filtered by user)
        # For Cognito mode, replace with query by userId
        logger.info(f"Scanning all items for all users, filter: {bought_filter}")

        response = table.scan()

        """
        # COGNITO MODE (commented out):
        # Query items for the user
        logger.info(f"Querying items for user: {user_id}, filter: {bought_filter}")

        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        """

        items = response.get('Items', [])

        # Apply bought filter if specified
        if bought_filter == 'true':
            items = [item for item in items if item.get('bought') is True]
        elif bought_filter == 'false':
            items = [item for item in items if item.get('bought') is False]

        # Sort by addedDate (most recent first)
        items.sort(key=lambda x: x.get('addedDate', ''), reverse=True)

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
