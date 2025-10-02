"""
Lambda function to create a new shopping list item in DynamoDB.

This function adds a new item to the ShoppingList table with auto-generated
itemId and timestamps.
"""

import json
import boto3
import uuid
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ShoppingList')


def lambda_handler(event, context):
    """
    Create a new shopping list item.

    Expected input (JSON):
    {
        "itemName": "Eggs",
        "quantity": 12,
        "category": "Dairy"  // optional
    }

    UserId is extracted from Cognito JWT token claims.

    Returns:
        dict: Response with status code and created item details
    """
    try:
        # Extract userId from Cognito authorizer claims
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('custom:displayName') or claims.get('email', '').split('@')[0]

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

        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        # Validate required fields
        required_fields = ['itemName', 'quantity']
        for field in required_fields:
            if field not in body:
                logger.error(f"Missing required field: {field}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Missing required field: {field}'
                    })
                }

        # Extract and validate data
        item_name = body['itemName']
        quantity = body['quantity']
        category = body.get('category', '')  # Optional field

        # Validate quantity is a positive number
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid quantity: {quantity}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Quantity must be a positive number'
                })
            }

        # Generate UUID and timestamp
        item_id = str(uuid.uuid4())
        added_date = datetime.utcnow().isoformat() + 'Z'

        # Create item object
        item = {
            'userId': user_id,
            'itemId': item_id,
            'itemName': item_name,
            'quantity': quantity,
            'bought': False,
            'addedDate': added_date
        }

        # Add category if provided
        if category:
            item['category'] = category

        # Insert item into DynamoDB
        logger.info(f"Creating item for user {user_id}: {item_name}")
        table.put_item(Item=item)

        logger.info(f"Successfully created item {item_id}")

        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Item created successfully',
                'item': item
            })
        }

    except Exception as e:
        logger.error(f"Error creating item: {str(e)}", exc_info=True)
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
