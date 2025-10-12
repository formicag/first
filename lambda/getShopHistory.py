"""
Lambda function to retrieve shop history from DynamoDB.

This function queries the ShoppingList-ShopHistory-Dev table to get
saved shopping trips with all items and spending data.
"""

import json
import boto3
import logging
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ShoppingList-ShopHistory-Dev')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON-serializable formats."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Retrieve shop history from DynamoDB.

    Query parameters:
    - limit: Number of shops to return (default: 10)

    Returns:
        dict: Response with status code and list of shop records
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', '10'))

        logger.info(f"Retrieving shop history, limit: {limit}")

        # Scan the table to get all shop records
        response = table.scan()

        shops = response.get('Items', [])

        # Sort by shopDate (most recent first)
        shops.sort(key=lambda x: x.get('shopDate', ''), reverse=True)

        # Limit the results
        shops = shops[:limit]

        logger.info(f"Retrieved {len(shops)} shop records")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'count': len(shops),
                'shops': shops
            }, cls=DecimalEncoder)
        }

    except ValueError as ve:
        logger.error(f"Invalid limit parameter: {str(ve)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid limit parameter',
                'message': str(ve)
            })
        }

    except Exception as e:
        logger.error(f"Error retrieving shop history: {str(e)}", exc_info=True)
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
