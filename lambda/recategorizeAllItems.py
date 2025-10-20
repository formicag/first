"""
Lambda function to recategorize ALL shopping list items using Amazon Bedrock.

This function updates categories for ALL items in DynamoDB, regardless of
whether they already have categories assigned.
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
    Recategorize ALL shopping list items using Bedrock AI.

    Expected input:
    {
        "userId": "Gianluca" or "Nicole" or "all"
    }

    Returns:
        dict: Response with status code and recategorization summary
    """
    try:
        # Extract userId from path parameters or body (or default to 'all')
        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userId', 'all')

        logger.info(f"=" * 80)
        logger.info(f"RECATEGORIZE ALL ITEMS - START")
        logger.info(f"User ID: {user_id}")
        logger.info(f"=" * 80)

        # Get all items (not just uncategorized)
        all_items = get_all_items(user_id)

        if not all_items:
            logger.info(f"No items found for user: {user_id}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'No items to recategorize',
                    'recategorizedCount': 0
                })
            }

        logger.info(f"Found {len(all_items)} total items in database")
        logger.info(f"Items breakdown by current category:")

        # Log current categories
        category_counts = {}
        for item in all_items:
            cat = item.get('category', 'NO_CATEGORY')
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for cat, count in sorted(category_counts.items()):
            logger.info(f"  - {cat}: {count} items")

        logger.info(f"-" * 80)
        logger.info(f"Starting recategorization...")
        logger.info(f"-" * 80)

        # Recategorize each item using Bedrock
        recategorized_count = 0
        category_changes = []
        errors = []

        for idx, item in enumerate(all_items, 1):
            try:
                item_name = item.get('itemName', 'Unknown')
                old_category = item.get('category', 'No category')
                user_id_item = item.get('userId', 'Unknown')
                item_id = item.get('itemId', 'Unknown')

                logger.info(f"[{idx}/{len(all_items)}] Processing: '{item_name}' (current: '{old_category}')")

                # Call AI to get new category
                logger.info(f"  → Calling Bedrock AI for '{item_name}'...")
                result = categorize_item_with_bedrock(item_name)
                new_category = result['category']

                logger.info(f"  → AI returned category: '{new_category}'")

                # Validate the new category
                if new_category not in UK_CATEGORIES and new_category != 'Uncategorized':
                    logger.warning(f"  ⚠️  AI returned INVALID category '{new_category}', using 'Uncategorized'")
                    new_category = 'Uncategorized'

                # Update item category in DynamoDB
                logger.info(f"  → Updating DynamoDB: userId={user_id_item}, itemId={item_id}")
                table.update_item(
                    Key={
                        'userId': item['userId'],
                        'itemId': item['itemId']
                    },
                    UpdateExpression='SET category = :category',
                    ExpressionAttributeValues={
                        ':category': new_category
                    }
                )

                # Track if category changed
                if old_category != new_category:
                    category_changes.append({
                        'itemName': item_name,
                        'oldCategory': old_category,
                        'newCategory': new_category
                    })
                    logger.info(f"  ✅ CHANGED: '{old_category}' → '{new_category}'")
                else:
                    logger.info(f"  ⏭️  UNCHANGED: '{new_category}'")

                recategorized_count += 1

            except Exception as e:
                error_msg = f"Error recategorizing item {item.get('itemName', 'Unknown')}: {str(e)}"
                logger.error(f"  ❌ ERROR: {error_msg}")
                errors.append(error_msg)

        logger.info(f"=" * 80)
        logger.info(f"RECATEGORIZATION COMPLETE")
        logger.info(f"Total items processed: {recategorized_count}")
        logger.info(f"Categories changed: {len(category_changes)}")
        logger.info(f"Errors: {len(errors)}")

        if category_changes:
            logger.info(f"Category changes:")
            for change in category_changes:
                logger.info(f"  - {change['itemName']}: {change['oldCategory']} → {change['newCategory']}")

        if errors:
            logger.error(f"Errors encountered:")
            for error in errors:
                logger.error(f"  - {error}")

        logger.info(f"=" * 80)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Recategorization complete',
                'recategorizedCount': recategorized_count,
                'totalFound': len(all_items),
                'categoryChangesCount': len(category_changes),
                'categoryChanges': category_changes[:20],  # Limit to first 20 for response size
                'errors': errors if errors else None
            })
        }

    except Exception as e:
        logger.error(f"Error in recategorization: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to recategorize items',
                'message': str(e)
            })
        }


def get_all_items(user_id):
    """
    Retrieve ALL items from DynamoDB (including those with categories).

    Args:
        user_id: User ID or "all" for all users

    Returns:
        list: All items
    """
    all_items = []

    if user_id.lower() == 'all':
        # Scan entire table for all items
        response = table.scan()
        all_items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_items.extend(response.get('Items', []))

    else:
        # Query for specific user
        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        all_items = response.get('Items', [])

    return all_items


def categorize_item_with_bedrock(item_name):
    """
    Use Amazon Bedrock to categorize a grocery item.

    Args:
        item_name: Name of the grocery item

    Returns:
        dict: Dictionary with 'category' key
    """
    logger.info(f"    🤖 Bedrock: Categorizing '{item_name}'")

    # Create prompt for Bedrock
    categories_str = ", ".join(UK_CATEGORIES)
    logger.info(f"    🤖 Bedrock: Using {len(UK_CATEGORIES)} categories")

    prompt = f"""You are categorizing grocery items for a UK supermarket. For this item: '{item_name}'

Categorize into ONE of these UK shopping centre aisles: {categories_str}

IMPORTANT - Consider the form/preparation:
- Fresh items (fresh fish, fresh meat, fresh produce) → use Fresh/Fish/Meat categories
- Canned items (tinned tuna, canned beans, jarred sauce) → use "Canned & Jarred"
- Frozen items (frozen peas, ice cream) → use "Frozen Foods"
- Ambient packaged items (pasta, rice, flour) → use "Pantry & Dry Goods"
- If item includes "tuna" without specifying fresh → assume CANNED (goes to "Canned & Jarred")
- If item includes "salmon" without specifying fresh → assume FRESH (goes to "Fish & Seafood")

Return ONLY valid JSON in this exact format:
{{"category": "category name"}}"""

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
        logger.info(f"    🤖 Bedrock: Invoking model {BEDROCK_MODEL_ID}")
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        # Parse response for Claude format
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text'].strip()
        logger.info(f"    🤖 Bedrock: Raw response: {response_text[:200]}")

        # Parse JSON response
        try:
            result = json.loads(response_text)
            category = result.get('category', 'Uncategorized')
            logger.info(f"    🤖 Bedrock: Parsed category: '{category}'")
        except json.JSONDecodeError as je:
            logger.error(f"    ❌ Bedrock: Invalid JSON response for '{item_name}': {response_text}")
            category = 'Uncategorized'

        # Validate category is in our list
        if category not in UK_CATEGORIES and category != 'Uncategorized':
            logger.warning(f"    ⚠️  Bedrock: Invalid category '{category}' for '{item_name}'. Using 'Uncategorized'.")
            category = 'Uncategorized'

        logger.info(f"    ✅ Bedrock: Final category: '{category}'")
        return {
            'category': category
        }

    except Exception as e:
        logger.error(f"    ❌ Bedrock: Error for '{item_name}': {str(e)}")
        return {
            'category': 'Uncategorized'
        }
