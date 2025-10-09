"""
Lambda function to create a new shopping list item in DynamoDB.

This function adds a new item to the ShoppingList table with auto-generated
itemId and timestamps. It automatically categorizes items using Amazon Bedrock.
"""

import json
import boto3
import uuid
from datetime import datetime
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
        "itemName": "Eggs",
        "quantity": 12,
        "category": "Dairy"  // optional
    }

    UserId is extracted from Cognito JWT token claims.

    Returns:
        dict: Response with status code and created item details
    """
    try:
        # BYPASS MODE: Use default user (no Cognito authentication)
        # Uncomment the code below to re-enable Cognito user extraction
        """
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
        """

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
        ai_result = process_item_with_ai(item_name, custom_prompt)

        corrected_name = ai_result['correctedName']
        category = ai_result['category']

        logger.info(f"AI processed: '{item_name}' → '{corrected_name}' ({category})")

        # Generate UUID and timestamp
        item_id = str(uuid.uuid4())
        added_date = datetime.utcnow().isoformat() + 'Z'

        # Create item object with AI-processed data
        item = {
            'userId': user_id,
            'itemId': item_id,
            'itemName': corrected_name,  # Use AI-corrected name
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
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Item created successfully',
                'item': item,
                'aiProcessing': {
                    'originalName': item_name,
                    'correctedName': corrected_name,
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


def process_item_with_ai(item_name, custom_prompt=''):
    """
    Use Amazon Bedrock to process a grocery item:
    1. Correct spelling
    2. Capitalize first letter of each word
    3. Categorize into UK shopping centre aisle

    Args:
        item_name: Name of the grocery item
        custom_prompt: Optional custom instructions to add to the AI prompt

    Returns:
        dict: Dictionary with 'correctedName' and 'category' keys
    """
    # Build categories string
    categories_str = ", ".join(UK_CATEGORIES)

    # Base prompt
    base_prompt = f"""You are a UK shopping assistant helping to process grocery items.

For this item: '{item_name}'

TASK 1 - Spelling Correction:
- Correct any spelling mistakes
- If spelling is already correct, keep the original name
- Ensure proper spacing

TASK 2 - Capitalization:
- Capitalize the FIRST letter of EACH word
- Examples: "pork chops" → "Pork Chops", "tomato" → "Tomato"

TASK 3 - Categorization:
- Categorize into ONE of these UK shopping centre aisles: {categories_str}
- Use standard UK supermarket terminology
- Think about where this would be found in a typical Tesco, Sainsbury's, or Asda"""

    # Add custom prompt if provided
    if custom_prompt and custom_prompt.strip():
        base_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt.strip()}"

    base_prompt += """\n\nReturn ONLY valid JSON in this exact format:
{"correctedName": "Item Name With Proper Capitalization", "category": "Category Name"}"""

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
            category = result.get('category', 'Uncategorized')

            # Validate category is in our list
            if category not in UK_CATEGORIES and category != 'Uncategorized':
                logger.warning(f"AI returned invalid category '{category}'. Using 'Uncategorized'.")
                category = 'Uncategorized'

            return {
                'correctedName': corrected_name,
                'category': category
            }

        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON from AI for '{item_name}': {response_text}")
            # Fallback: capitalize first letter of each word manually
            corrected_name = ' '.join(word.capitalize() for word in item_name.split())
            return {
                'correctedName': corrected_name,
                'category': 'Uncategorized'
            }

    except Exception as e:
        logger.error(f"Error calling Bedrock for '{item_name}': {str(e)}")
        # Fallback: capitalize first letter of each word manually
        corrected_name = ' '.join(word.capitalize() for word in item_name.split())
        return {
            'correctedName': corrected_name,
            'category': 'Uncategorized'
        }
