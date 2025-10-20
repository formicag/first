"""
Lambda function to recategorize ALL shopping list items using Amazon Bedrock.

This function updates categories for ALL items in DynamoDB, regardless of
whether they already have categories assigned.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging
import time

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

# Rule-based fallback categorization - NEVER returns "Uncategorized"
def fallback_categorize(item_name):
    """
    Rule-based categorizer for when AI fails. NEVER returns "Uncategorized".
    Uses keyword matching and smart defaults.
    """
    item_lower = item_name.lower().strip()

    # Dairy & Eggs
    if any(word in item_lower for word in ['milk', 'butter', 'cheese', 'yogurt', 'yoghurt', 'cream', 'eggs', 'egg']):
        return "Dairy & Eggs"

    # Meat & Poultry
    if any(word in item_lower for word in ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'sausage', 'bacon', 'ham', 'chops', 'steak', 'mince']):
        return "Meat & Poultry"

    # Fish & Seafood
    if any(word in item_lower for word in ['salmon', 'tuna', 'cod', 'fish', 'prawns', 'shrimp', 'seafood']):
        # Check if it's canned
        if any(word in item_lower for word in ['canned', 'tinned', 'can', 'tin']):
            return "Canned & Jarred"
        return "Fish & Seafood"

    # Bakery & Bread
    if any(word in item_lower for word in ['bread', 'baguette', 'rolls', 'buns', 'bagels', 'croissant', 'rye']):
        return "Bakery & Bread"

    # Fresh Produce - Fruit
    if any(word in item_lower for word in ['apple', 'banana', 'orange', 'grape', 'berry', 'melon', 'mango', 'pear', 'peach', 'plum', 'kiwi', 'pineapple', 'lemon', 'lime']):
        return "Fresh Produce - Fruit"

    # Fresh Produce - Vegetables
    if any(word in item_lower for word in ['potato', 'carrot', 'onion', 'tomato', 'pepper', 'broccoli', 'cauliflower', 'cabbage', 'lettuce', 'cucumber', 'courgette', 'aubergine', 'mushroom', 'vegetables']):
        # Check if frozen
        if 'frozen' in item_lower:
            return "Frozen Foods"
        return "Fresh Produce - Vegetables"

    # Fresh Produce - Herbs & Salads
    if any(word in item_lower for word in ['herb', 'basil', 'parsley', 'coriander', 'mint', 'salad', 'tzatziki', 'hummus']):
        return "Fresh Produce - Herbs & Salads"

    # Frozen Foods
    if any(word in item_lower for word in ['frozen', 'ice cream', 'chips']) and 'frozen' in item_lower:
        return "Frozen Foods"

    # Health & Beauty
    if any(word in item_lower for word in ['shampoo', 'soap', 'toothpaste', 'toothbrush', 'deodorant', 'face wash', 'cotton wool', 'hand wash', 'cetirizine', 'contact lens', 'neutrogena']):
        return "Health & Beauty"

    # Household & Cleaning
    if any(word in item_lower for word in ['cleaning', 'cleaner', 'detergent', 'washing', 'dishwasher', 'toilet', 'bleach', 'domestos', 'bags', 'bin', 'tissue', 'kitchen roll', 'air freshener']):
        return "Household & Cleaning"

    # Beverages
    if any(word in item_lower for word in ['water', 'juice', 'coffee', 'tea', 'teabags', 'cola', 'lemonade', 'drink', 'kombucha', 'kambucha', 'kefir']):
        return "Beverages"

    # Alcohol & Wine
    if any(word in item_lower for word in ['beer', 'wine', 'vodka', 'whisky', 'gin', 'rum', 'alcohol', 'cider', 'lager']):
        return "Alcohol & Wine"

    # Snacks & Confectionery
    if any(word in item_lower for word in ['chocolate', 'crisps', 'chips', 'biscuit', 'cookie', 'sweet', 'candy', 'bounty', 'snack']):
        return "Snacks & Confectionery"

    # Canned & Jarred
    if any(word in item_lower for word in ['canned', 'tinned', 'can', 'tin', 'jar', 'jarred', 'tuna can']):
        return "Canned & Jarred"

    # Pantry & Dry Goods (most generic fallback - handles: rice, pasta, flour, lentils, etc.)
    logger.warning(f"No specific category match for '{item_name}'. Using Pantry & Dry Goods as default.")
    return "Pantry & Dry Goods"


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
        skipped_count = 0

        for idx, item in enumerate(all_items, 1):
            # Add delay to avoid Bedrock throttling (except for first item)
            if idx > 1:
                time.sleep(0.8)  # 800ms delay between API calls
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
                if new_category not in UK_CATEGORIES:
                    logger.warning(f"  ⚠️  AI returned INVALID category '{new_category}', using fallback categorization")
                    new_category = fallback_categorize(item_name)

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
                skipped_count += 1

        # Calculate success metrics
        total_items = len(all_items)
        successful_items = recategorized_count
        failed_items = total_items - successful_items

        logger.info(f"=" * 80)
        logger.info(f"RECATEGORIZATION COMPLETE")
        logger.info(f"Total items found: {total_items}")
        logger.info(f"Successfully processed: {successful_items}")
        logger.info(f"Failed/Skipped: {failed_items}")
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
                'totalItems': total_items,
                'successfulItems': successful_items,
                'failedItems': failed_items,
                'recategorizedCount': recategorized_count,
                'categoryChangesCount': len(category_changes),
                'categoryChanges': category_changes[:20],  # Limit to first 20 for response size
                'errors': errors[:10] if errors else None,  # Limit to first 10 errors
                'hasErrors': len(errors) > 0,
                'completed': failed_items == 0
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
            category = result.get('category')
            if not category:
                logger.warning(f"    ⚠️  Bedrock: No category in response for '{item_name}'. Using fallback.")
                category = fallback_categorize(item_name)
            logger.info(f"    🤖 Bedrock: Parsed category: '{category}'")
        except json.JSONDecodeError as je:
            logger.error(f"    ❌ Bedrock: Invalid JSON response for '{item_name}': {response_text}")
            category = fallback_categorize(item_name)

        # Validate category is in our list
        if category not in UK_CATEGORIES:
            logger.warning(f"    ⚠️  Bedrock: Invalid category '{category}' for '{item_name}'. Using fallback.")
            category = fallback_categorize(item_name)

        logger.info(f"    ✅ Bedrock: Final category: '{category}'")
        return {
            'category': category
        }

    except Exception as e:
        logger.error(f"    ❌ Bedrock: Error for '{item_name}': {str(e)}")
        return {
            'category': fallback_categorize(item_name)
        }
