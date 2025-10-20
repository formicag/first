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
BEDROCK_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'

# UK Shopping Centre Standard Categories (16 Total)
# These MUST match store_layout.py exactly for proper sorting
UK_CATEGORIES = [
    "Fresh Produce - Fruit",
    "Fresh Produce - Vegetables",
    "Fresh Produce - Herbs & Salads",
    "Meat & Poultry",
    "Fish & Seafood",
    "Dairy & Eggs",
    "Bakery & Bread",
    "Frozen Foods",
    "Pantry & Dry Goods",
    "Canned & Jarred",
    "Snacks & Confectionery",
    "Beverages",
    "Alcohol & Wine",
    "Health & Beauty",
    "Household & Cleaning",
    "Baby & Child"
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
        spelling_corrected_count = 0
        spelling_corrections = []
        errors = []

        for item in uncategorized_items:
            try:
                item_name = item.get('itemName', 'Unknown')
                result = categorize_item_with_bedrock(item_name)

                # Prepare update expression
                update_expression = 'SET category = :category'
                expression_values = {':category': result['category']}

                # Check if spelling was corrected
                if result['correctedName'] != item_name:
                    update_expression += ', itemName = :itemName'
                    expression_values[':itemName'] = result['correctedName']
                    spelling_corrected_count += 1
                    spelling_corrections.append({
                        'original': item_name,
                        'corrected': result['correctedName']
                    })
                    logger.info(f"Corrected spelling: '{item_name}' → '{result['correctedName']}'")

                # Update item in DynamoDB
                table.update_item(
                    Key={
                        'userId': item['userId'],
                        'itemId': item['itemId']
                    },
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )

                logger.info(f"Categorized '{result['correctedName']}' as '{result['category']}'")
                categorized_count += 1

            except Exception as e:
                error_msg = f"Error categorizing item {item.get('itemName', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"Successfully categorized {categorized_count} items, corrected {spelling_corrected_count} spellings")

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
                'spellingCorrectedCount': spelling_corrected_count,
                'spellingCorrections': spelling_corrections,
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
    Use Amazon Bedrock to categorize a grocery item and correct spelling.

    Args:
        item_name: Name of the grocery item

    Returns:
        dict: Dictionary with 'correctedName' and 'category' keys
    """
    # Create prompt for Bedrock
    categories_str = ", ".join(UK_CATEGORIES)
    prompt = f"""You are categorizing grocery items for a UK supermarket. For this item: '{item_name}'

Task 1: Correct any spelling mistakes in the item name. If spelling is correct, return the original name.
Task 2: Categorize into ONE of these UK shopping centre aisles: {categories_str}

IMPORTANT - Consider the form/preparation:
- Fresh items (fresh fish, fresh meat, fresh produce) → use Fresh/Fish/Meat categories
- Canned items (tinned tuna, canned beans, jarred sauce) → use "Canned & Jarred"
- Frozen items (frozen peas, ice cream) → use "Frozen Foods"
- Ambient packaged items (pasta, rice, flour) → use "Pantry & Dry Goods"
- If item includes "tuna" without specifying fresh → assume CANNED (goes to "Canned & Jarred")
- If item includes "salmon" without specifying fresh → assume FRESH (goes to "Fish & Seafood")

Return ONLY valid JSON in this exact format:
{{"correctedName": "corrected item name", "category": "category name"}}"""

    # Prepare request for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        # Parse response for Claude format
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text'].strip()

        # Parse JSON response
        try:
            result = json.loads(response_text)
            corrected_name = result.get('correctedName', item_name)
            category = result.get('category', 'Uncategorized')
        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON response from Bedrock for item '{item_name}': {response_text}")
            # Fallback to original name and Uncategorized
            corrected_name = item_name
            category = 'Uncategorized'

        # Validate category is in our list
        if category not in UK_CATEGORIES and category != 'Uncategorized':
            logger.warning(f"Bedrock returned invalid category '{category}' for item '{item_name}'. Using 'Uncategorized'.")
            category = 'Uncategorized'

        return {
            'correctedName': corrected_name,
            'category': category
        }

    except Exception as e:
        logger.error(f"Error calling Bedrock for item '{item_name}': {str(e)}")
        return {
            'correctedName': item_name,
            'category': 'Uncategorized'
        }
