"""
Lambda function to create a new shopping list item in DynamoDB.

This function adds a new item to the ShoppingList table with auto-generated
itemId and timestamps. It automatically categorizes items using Amazon Bedrock.
"""

import json
import boto3
import uuid
import os
from datetime import datetime
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='eu-west-1')
table = dynamodb.Table('ShoppingList')

# Bedrock model configuration - configurable via environment variable
BEDROCK_MODEL_ID = os.environ.get(
    'BEDROCK_MODEL',
    'anthropic.claude-3-haiku-20240307-v1:0'
)

# UK Shopping Centre Standard Categories
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
    Create a new shopping list item.

    Expected input (JSON):
    {
        "userId": "Gianluca",
        "itemName": "Eggs",
        "quantity": 12,
        "category": "Dairy"  // optional
    }

    Returns:
        dict: Response with status code and created item details
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        # Get userId from request body (allows frontend to specify which user's list)
        user_id = body.get('userId', 'TestUser')

        logger.info(f"Creating item for userId: {user_id}")

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
        custom_prompt = body.get('customPrompt', '')  # Optional AI prompt customization
        context_items = body.get('contextItems', [])  # Household-specific context
        use_uk_english = body.get('useUKEnglish', True)  # UK English preference
        strict_categories = body.get('strictCategories', True)  # Strict UK categories

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

        # Use AI to process item name: spell check, capitalize, and categorize
        logger.info(f"Processing item with AI: {item_name}")
        ai_result = process_item_with_ai(
            item_name,
            custom_prompt,
            context_items,
            use_uk_english,
            strict_categories
        )

        corrected_name = ai_result['correctedName']
        estimated_price = ai_result['estimatedPrice']
        category = ai_result['category']

        logger.info(f"AI processed: '{item_name}' → '{corrected_name}' (£{estimated_price:.2f}, {category})")

        # Generate UUID and timestamp
        item_id = str(uuid.uuid4())
        added_date = datetime.utcnow().isoformat() + 'Z'

        # Create item object with AI-processed data
        item = {
            'userId': user_id,
            'itemId': item_id,
            'itemName': corrected_name,  # Use AI-corrected name
            'estimatedPrice': Decimal(str(estimated_price)),  # Convert to Decimal for DynamoDB
            'quantity': quantity,
            'category': category,  # Use AI-assigned category
            'bought': False,
            'addedDate': added_date
        }

        # Insert item into DynamoDB
        logger.info(f"Creating item for user {user_id}: {corrected_name}")
        table.put_item(Item=item)

        logger.info(f"Successfully created item {item_id}")

        # Return success response with AI processing details
        # Convert Decimal to float for JSON serialization
        response_item = {
            'userId': item['userId'],
            'itemId': item['itemId'],
            'itemName': item['itemName'],
            'estimatedPrice': float(item['estimatedPrice']),
            'quantity': item['quantity'],
            'category': item['category'],
            'bought': item['bought'],
            'addedDate': item['addedDate']
        }

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Item created successfully',
                'item': response_item,
                'aiProcessing': {
                    'originalName': item_name,
                    'correctedName': corrected_name,
                    'estimatedPrice': estimated_price,
                    'wasSpellCorrected': item_name != corrected_name,
                    'category': category
                }
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


def process_item_with_ai(item_name, custom_prompt='', context_items=[], use_uk_english=True, strict_categories=True):
    """
    Use Amazon Bedrock to process a grocery item:
    1. Correct spelling
    2. Capitalize first letter of each word
    3. Categorize into UK shopping centre aisle

    Args:
        item_name: Name of the grocery item
        custom_prompt: Optional custom instructions to add to the AI prompt
        context_items: List of {term, meaning} dictionaries for household-specific context
        use_uk_english: Whether to enforce UK English spelling and terminology
        strict_categories: Whether to strictly use UK supermarket category names

    Returns:
        dict: Dictionary with 'correctedName' and 'category' keys
    """
    # Build categories string
    categories_str = ", ".join(UK_CATEGORIES)

    # Base prompt
    base_prompt = f"""You are a UK shopping assistant helping to process grocery items.

For this item: '{item_name}'"""

    # Add UK English instruction if enabled
    if use_uk_english:
        base_prompt += """

IMPORTANT: Use UK English spelling and terminology.
Examples: colour (not color), flavour (not flavor), courgette (not zucchini), aubergine (not eggplant)"""

    # Add household context if provided
    if context_items:
        base_prompt += "\n\nHOUSEHOLD CONTEXT (Gianluca and Nicole's specific meanings):\n"
        for item in context_items:
            base_prompt += f"- \"{item['term']}\" means {item['meaning']}\n"

    base_prompt += """

TASK 1 - Spelling Correction:
- Correct any spelling mistakes
- If spelling is already correct, keep the original name
- Ensure proper spacing

TASK 2 - Capitalization:
- Capitalize the FIRST letter of EACH word
- Examples: "pork chops" → "Pork Chops", "tomato" → "Tomato"

TASK 3 - Price Estimation:
- Estimate the typical price at Sainsbury's UK for this item
- Consider the quantity mentioned (if any) or assume standard pack size
- Return price in GBP (pounds) as a decimal number
- Examples: "Milk" → 1.25, "Bread" → 1.10, "Apples" (per kg) → 2.50
- Use typical 2024-2025 Sainsbury's pricing
- For unclear quantities, estimate for a typical single purchase unit
"""

    # Add categorization task
    if strict_categories:
        base_prompt += f"""
TASK 4 - Categorization:
- Categorize into ONE of these UK shopping centre aisles: {categories_str}
- Use standard UK supermarket terminology
- Think about where this would be found in a typical Tesco, Sainsbury's, or Asda"""
    else:
        base_prompt += f"""
TASK 4 - Categorization:
- Categorize into ONE of these UK shopping centre aisles: {categories_str}
- You may suggest alternative category names if more appropriate"""

    # Add custom prompt if provided
    if custom_prompt and custom_prompt.strip():
        base_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt.strip()}"

    base_prompt += """\n\nReturn ONLY valid JSON in this exact format:
{"correctedName": "Item Name With Proper Capitalization", "estimatedPrice": 1.25, "category": "Category Name"}"""

    # Prepare request for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "temperature": 0,  # Deterministic output
        "messages": [
            {
                "role": "user",
                "content": base_prompt
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

        # Parse response
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text'].strip()

        # Parse JSON response
        try:
            result = json.loads(response_text)
            corrected_name = result.get('correctedName', item_name)
            estimated_price = result.get('estimatedPrice', 0.0)  # Default to 0 if no price
            category = result.get('category', 'Uncategorized')

            # Validate category is in our list
            if category not in UK_CATEGORIES and category != 'Uncategorized':
                logger.warning(f"AI returned invalid category '{category}'. Using 'Uncategorized'.")
                category = 'Uncategorized'

            # Validate price is a positive number
            try:
                estimated_price = float(estimated_price)
                if estimated_price < 0:
                    estimated_price = 0.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid price '{estimated_price}'. Using 0.0")
                estimated_price = 0.0

            return {
                'correctedName': corrected_name,
                'estimatedPrice': estimated_price,
                'category': category
            }

        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON from AI for '{item_name}': {response_text}")
            # Fallback: capitalize first letter of each word manually
            corrected_name = ' '.join(word.capitalize() for word in item_name.split())
            return {
                'correctedName': corrected_name,
                'estimatedPrice': 0.0,
                'category': 'Uncategorized'
            }

    except Exception as e:
        logger.error(f"Error calling Bedrock for '{item_name}': {str(e)}")
        # Fallback: capitalize first letter of each word manually
        corrected_name = ' '.join(word.capitalize() for word in item_name.split())
        return {
            'correctedName': corrected_name,
            'estimatedPrice': 0.0,
            'category': 'Uncategorized'
        }
