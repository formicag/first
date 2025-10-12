"""
Lambda function to update a shopping list item in DynamoDB.

This function updates specified fields of an existing item and automatically
sets boughtDate when bought status changes to true.
"""

import json
import boto3
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
    Update an existing shopping list item.

    Expected input (JSON):
    {
        "userId": "Gianluca",
        "itemId": "550e8400-e29b-41d4-a716-446655440001",
        "itemName": "Whole Milk",      // optional
        "quantity": 3,                  // optional
        "bought": true,                 // optional
        "category": "Dairy"            // optional
    }

    Returns:
        dict: Response with status code and updated item details
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

        # Parse body for update fields
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Check if item exists
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
        except Exception as e:
            logger.error(f"Error checking item existence: {str(e)}")
            raise

        # Build update expression dynamically
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        # Handle itemName update
        if 'itemName' in body:
            update_expression_parts.append('#itemName = :itemName')
            expression_attribute_names['#itemName'] = 'itemName'
            expression_attribute_values[':itemName'] = body['itemName']

        # Handle quantity update
        if 'quantity' in body:
            try:
                quantity = int(body['quantity'])
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
                update_expression_parts.append('#quantity = :quantity')
                expression_attribute_names['#quantity'] = 'quantity'
                expression_attribute_values[':quantity'] = quantity
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid quantity: {body['quantity']}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Quantity must be a positive number'
                    })
                }

        # Handle category update
        if 'category' in body:
            update_expression_parts.append('#category = :category')
            expression_attribute_names['#category'] = 'category'
            expression_attribute_values[':category'] = body['category']

        # Handle bought status update
        if 'bought' in body:
            bought_value = body['bought']
            if not isinstance(bought_value, bool):
                logger.error(f"Invalid bought value: {bought_value}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'bought field must be a boolean'
                    })
                }

            update_expression_parts.append('#bought = :bought')
            expression_attribute_names['#bought'] = 'bought'
            expression_attribute_values[':bought'] = bought_value

            # Set boughtDate if marking as bought
            if bought_value is True:
                bought_date = datetime.utcnow().isoformat() + 'Z'
                update_expression_parts.append('#boughtDate = :boughtDate')
                expression_attribute_names['#boughtDate'] = 'boughtDate'
                expression_attribute_values[':boughtDate'] = bought_date
            else:
                # Clear boughtDate if marking as not bought
                update_expression_parts.append('#boughtDate = :boughtDate')
                expression_attribute_names['#boughtDate'] = 'boughtDate'
                expression_attribute_values[':boughtDate'] = None

        # Handle saveForNext status update
        if 'saveForNext' in body:
            save_for_next_value = body['saveForNext']
            if not isinstance(save_for_next_value, bool):
                logger.error(f"Invalid saveForNext value: {save_for_next_value}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'saveForNext field must be a boolean'
                    })
                }

            update_expression_parts.append('#saveForNext = :saveForNext')
            expression_attribute_names['#saveForNext'] = 'saveForNext'
            expression_attribute_values[':saveForNext'] = save_for_next_value

        # Check if there are any fields to update
        if not update_expression_parts:
            logger.error("No fields to update")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No fields to update. Provide at least one of: itemName, quantity, bought, category'
                })
            }

        # Build final update expression
        update_expression = 'SET ' + ', '.join(update_expression_parts)

        # Update item in DynamoDB
        logger.info(f"Updating item {item_id} for user {user_id}")

        response = table.update_item(
            Key={
                'userId': user_id,
                'itemId': item_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )

        updated_item = response['Attributes']

        logger.info(f"Successfully updated item {item_id}")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Item updated successfully',
                'item': updated_item
            }, default=str)
        }

    except Exception as e:
        logger.error(f"Error updating item: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
