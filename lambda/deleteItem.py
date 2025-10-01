"""
Lambda function to delete a shopping list item from DynamoDB.

This function removes an item from the ShoppingList table.
"""

import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ShoppingList')


def lambda_handler(event, context):
    """
    Delete a shopping list item.

    Expected input (JSON):
    {
        "userId": "Gianluca",
        "itemId": "550e8400-e29b-41d4-a716-446655440001"
    }

    Returns:
        dict: Response with status code and deletion confirmation
    """
    try:
        # Extract path parameters
        path_params = event.get('pathParameters', {})
        user_id = path_params.get('userId')
        item_id = path_params.get('itemId')

        # Validate required path parameters
        if not user_id or not item_id:
            logger.error("Missing required path parameters: userId and/or itemId")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required path parameters: userId and itemId'
                })
            }

        # Check if item exists before deleting
        try:
            response = table.get_item(
                Key={
                    'userId': user_id,
                    'itemId': item_id
                }
            )
            if 'Item' not in response:
                logger.error(f"Item not found: {item_id} for user {user_id}")
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'error': 'Item not found'
                    })
                }

            # Store item details for response
            deleted_item = response['Item']

        except Exception as e:
            logger.error(f"Error checking item existence: {str(e)}")
            raise

        # Delete item from DynamoDB
        logger.info(f"Deleting item {item_id} for user {user_id}")

        table.delete_item(
            Key={
                'userId': user_id,
                'itemId': item_id
            }
        )

        logger.info(f"Successfully deleted item {item_id}")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Item deleted successfully',
                'deletedItem': {
                    'userId': user_id,
                    'itemId': item_id,
                    'itemName': deleted_item.get('itemName', 'Unknown')
                }
            })
        }

    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
