"""
Lambda function to recalculate prices for all items in DynamoDB.

This function scans all items and uses Amazon Bedrock to estimate
current Sainsbury's prices, updating the estimatedPrice field.
"""

import json
import boto3
import os
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


def lambda_handler(event, context):
    """
    Recalculate prices for all items in the shopping list.

    Returns:
        dict: Response with status code and update summary
    """
    try:
        logger.info("Starting price recalculation for all items")

        # Scan all items from DynamoDB
        response = table.scan()
        items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        logger.info(f"Found {len(items)} total items to process")

        if len(items) == 0:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'No items to recalculate',
                    'totalItems': 0,
                    'updatedCount': 0
                })
            }

        # Batch process items with AI - get all prices in one call for efficiency
        item_names = [item.get('itemName', '') for item in items]

        logger.info(f"Requesting prices for {len(item_names)} items from AI")
        prices_dict = get_bulk_prices(item_names)

        updated_count = 0
        failed_count = 0

        # Update each item with new price
        for item in items:
            user_id = item.get('userId')
            item_id = item.get('itemId')
            item_name = item.get('itemName', '')

            if not user_id or not item_id or not item_name:
                logger.warning(f"Skipping item with missing fields: {item}")
                failed_count += 1
                continue

            # Get price from AI response
            new_price = prices_dict.get(item_name, 0.0)

            logger.info(f"Updating {item_name}: £{new_price:.2f}")

            try:
                # Update item in DynamoDB - convert to Decimal
                table.update_item(
                    Key={
                        'userId': user_id,
                        'itemId': item_id
                    },
                    UpdateExpression='SET estimatedPrice = :price',
                    ExpressionAttributeValues={
                        ':price': Decimal(str(new_price))
                    }
                )
                updated_count += 1

            except Exception as e:
                logger.error(f"Error updating item {item_id}: {str(e)}")
                failed_count += 1

        logger.info(f"Recalculation complete: {updated_count} updated, {failed_count} failed")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Price recalculation complete',
                'totalItems': len(items),
                'updatedCount': updated_count,
                'failedCount': failed_count,
                'priceUpdates': {k: round(v, 2) for k, v in prices_dict.items()}
            })
        }

    except Exception as e:
        logger.error(f"Error during price recalculation: {str(e)}", exc_info=True)
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


def get_bulk_prices(item_names):
    """
    Use Amazon Bedrock to get prices for multiple items at once.

    Args:
        item_names: List of item names to price

    Returns:
        dict: Dictionary mapping item names to estimated prices
    """
    if not item_names:
        return {}

    # Build prompt for bulk pricing
    items_list = "\n".join([f"- {name}" for name in item_names])

    prompt = f"""You are a UK grocery pricing expert for Sainsbury's supermarket.

I need you to estimate the typical current price (2024-2025) at Sainsbury's UK for each of these grocery items:

{items_list}

For each item:
- Estimate the typical price for a standard purchase unit/pack size
- Use current Sainsbury's UK pricing knowledge
- Return price in GBP (pounds) as a decimal number
- Be realistic and accurate based on typical 2024-2025 prices

Return ONLY a valid JSON object mapping each item name to its price:
{{"Item Name": 1.25, "Another Item": 2.50}}

IMPORTANT: Use the exact item names from the list above as keys."""

    # Prepare request for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "temperature": 0,  # Deterministic output
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

        # Parse response
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text'].strip()

        logger.info(f"AI response: {response_text}")

        # Parse JSON response
        try:
            prices_dict = json.loads(response_text)

            # Validate and clean prices
            cleaned_prices = {}
            for item_name, price in prices_dict.items():
                try:
                    price_float = float(price)
                    if price_float < 0:
                        price_float = 0.0
                    cleaned_prices[item_name] = price_float
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price for '{item_name}': {price}")
                    cleaned_prices[item_name] = 0.0

            return cleaned_prices

        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON from AI: {response_text}")
            # Fallback: return 0.0 for all items
            return {name: 0.0 for name in item_names}

    except Exception as e:
        logger.error(f"Error calling Bedrock: {str(e)}")
        # Fallback: return 0.0 for all items
        return {name: 0.0 for name in item_names}
