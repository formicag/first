"""
Lambda function to delete a shop from shop history.

This function deletes a specific shop record from the ShoppingList-ShopHistory-Dev table.
"""

import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ShoppingList-ShopHistory-Dev')


def lambda_handler(event, context):
    """
    Delete a shop from shop history.

    Path parameters:
    - shopId: The ID of the shop to delete

    Returns:
        dict: Response with status code and success message
    """
    try:
        # Get shopId from path parameters
        path_params = event.get('pathParameters', {}) or {}
        shop_id = path_params.get('shopId')

        if not shop_id:
            logger.error("Missing shopId in path parameters")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameter: shopId'
                })
            }

        logger.info(f"Deleting shop with ID: {shop_id}")

        # First, get the shop to retrieve the shopDate (sort key)
        response = table.scan(
            FilterExpression='shopId = :sid',
            ExpressionAttributeValues={
                ':sid': shop_id
            }
        )

        items = response.get('Items', [])

        if not items:
            logger.warning(f"Shop not found: {shop_id}")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Shop not found'
                })
            }

        shop = items[0]
        shop_date = shop.get('shopDate')

        # Delete the shop using both partition key and sort key
        table.delete_item(
            Key={
                'shopId': shop_id,
                'shopDate': shop_date
            }
        )

        logger.info(f"Successfully deleted shop {shop_id}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Shop deleted successfully',
                'shopId': shop_id
            })
        }

    except Exception as e:
        logger.error(f"Error deleting shop: {str(e)}", exc_info=True)
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
