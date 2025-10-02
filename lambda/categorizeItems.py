"""
Lambda function to auto-categorize shopping list items using Amazon Bedrock.

This function queries uncategorized items from DynamoDB and uses Bedrock
to intelligently assign categories based on item names.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='eu-west-1')
table = dynamodb.Table('ShoppingList')

# Bedrock model configuration
BEDROCK_MODEL_ID = 'amazon.nova-micro-v1:0'

# Standard grocery categories
CATEGORIES = [
    "Fresh Produce - Fruit",
    "Fresh Produce - Vegetables",
    "Fresh Produce - Herbs",
    "Bakery",
    "Meat Fish & Deli",
    "Dairy & Eggs",
    "Frozen Foods",
    "Pantry / Dry Goods",
    "Snacks & Confectionery",
    "Beverages",
    "Household & Cleaning",
    "Health & Beauty"
]


def lambda_handler(event, context):
    """
    Auto-categorize shopping list items using Bedrock AI.

    Expected input:
    {
        "userId": "Gianluca" or "Nicole" or "all"
    }

    Returns:
        dict: Response with status code and categorization summary
    """
    try:
        # Extract userId from path parameters
        path_params = event.get('pathParameters', {})
        user_id = path_params.get('userId')

        if not user_id:
            logger.error("Missing required parameter: userId")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameter: userId'
                })
            }

        logger.info(f"Categorizing items for user: {user_id}")

        # Get uncategorized items
        uncategorized_items = get_uncategorized_items(user_id)

        if not uncategorized_items:
            logger.info(f"No uncategorized items found for user: {user_id}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'No items to categorize',
                    'categorizedCount': 0
                })
            }

        logger.info(f"Found {len(uncategorized_items)} uncategorized items")

        # Categorize each item using Bedrock
        categorized_count = 0
        errors = []

        for item in uncategorized_items:
            try:
                item_name = item.get('itemName', 'Unknown')
                category = categorize_item_with_bedrock(item_name)

                # Update item in DynamoDB
                table.update_item(
                    Key={
                        'userId': item['userId'],
                        'itemId': item['itemId']
                    },
                    UpdateExpression='SET category = :category',
                    ExpressionAttributeValues={
                        ':category': category
                    }
                )

                logger.info(f"Categorized '{item_name}' as '{category}'")
                categorized_count += 1

            except Exception as e:
                error_msg = f"Error categorizing item {item.get('itemName', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"Successfully categorized {categorized_count} items")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Categorization complete',
                'categorizedCount': categorized_count,
                'totalFound': len(uncategorized_items),
                'errors': errors if errors else None
            })
        }

    except Exception as e:
        logger.error(f"Error in categorization: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to categorize items',
                'message': str(e)
            })
        }


def get_uncategorized_items(user_id):
    """
    Retrieve items without categories from DynamoDB.

    Args:
        user_id: User ID or "all" for all users

    Returns:
        list: Items without categories
    """
    uncategorized_items = []

    if user_id.lower() == 'all':
        # Scan entire table for uncategorized items
        response = table.scan(
            FilterExpression=Attr('category').not_exists() | Attr('category').eq('')
        )
        uncategorized_items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('category').not_exists() | Attr('category').eq(''),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            uncategorized_items.extend(response.get('Items', []))

    else:
        # Query for specific user
        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id),
            FilterExpression=Attr('category').not_exists() | Attr('category').eq('')
        )
        uncategorized_items = response.get('Items', [])

    return uncategorized_items


def categorize_item_with_bedrock(item_name):
    """
    Use Amazon Bedrock to categorize a grocery item.

    Args:
        item_name: Name of the grocery item

    Returns:
        str: Category name
    """
    # Create prompt for Bedrock
    categories_str = ", ".join(CATEGORIES)
    prompt = f"""Categorize this grocery item into ONE of these categories: {categories_str}.

Item: {item_name}

Return ONLY the category name, nothing else. If unsure, return 'Unknown Category'."""

    # Prepare request for Amazon Nova
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "inferenceConfig": {
            "temperature": 0,
            "max_new_tokens": 50
        }
    }

    try:
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        # Parse response for Nova format
        response_body = json.loads(response['body'].read())
        category = response_body['output']['message']['content'][0]['text'].strip()

        # Validate category is in our list
        if category not in CATEGORIES and category != 'Unknown Category':
            logger.warning(f"Bedrock returned invalid category '{category}' for item '{item_name}'. Using 'Unknown Category'.")
            category = 'Unknown Category'

        return category

    except Exception as e:
        logger.error(f"Error calling Bedrock for item '{item_name}': {str(e)}")
        return 'Unknown Category'
