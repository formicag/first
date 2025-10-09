#!/bin/bash

# Script to backfill emojis for existing DynamoDB items
# This uses AWS CLI to scan items and update them with emojis

echo "Starting emoji backfill for existing items..."

# Get all items from DynamoDB
aws dynamodb scan \
    --table-name ShoppingList \
    --region eu-west-1 \
    --output json > /tmp/all_items.json

# Count items
TOTAL_ITEMS=$(cat /tmp/all_items.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)['Items']))")
echo "Found $TOTAL_ITEMS items in DynamoDB"

# Process each item with Python
python3 << 'EOF'
import json
import boto3

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='eu-west-1')
bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')

# Load items
with open('/tmp/all_items.json', 'r') as f:
    data = json.load(f)
    items = data['Items']

print(f"Processing {len(items)} items...")

# Simple emoji mapping based on common food items
EMOJI_MAP = {
    'milk': '🥛', 'bread': '🍞', 'eggs': '🥚', 'cheese': '🧀',
    'butter': '🧈', 'apple': '🍎', 'banana': '🍌', 'orange': '🍊',
    'tomato': '🍅', 'potato': '🥔', 'carrot': '🥕', 'onion': '🧅',
    'chicken': '🍗', 'beef': '🥩', 'fish': '🐟', 'bacon': '🥓',
    'pasta': '🍝', 'rice': '🍚', 'pizza': '🍕', 'sandwich': '🥪',
    'salad': '🥗', 'soup': '🍲', 'coffee': '☕', 'tea': '🍵',
    'water': '💧', 'juice': '🧃', 'wine': '🍷', 'beer': '🍺',
    'chocolate': '🍫', 'cookie': '🍪', 'cake': '🍰', 'ice cream': '🍦',
    'strawberry': '🍓', 'grape': '🍇', 'watermelon': '🍉', 'lemon': '🍋',
    'avocado': '🥑', 'broccoli': '🥦', 'mushroom': '🍄', 'corn': '🌽',
    'pepper': '🌶️', 'garlic': '🧄', 'ginger': '🫚', 'cucumber': '🥒',
    'lettuce': '🥬', 'cabbage': '🥬', 'spinach': '🥬', 'kale': '🥬',
    'pork': '🥓', 'lamb': '🥩', 'turkey': '🦃', 'sausage': '🌭',
    'shrimp': '🦐', 'crab': '🦀', 'lobster': '🦞', 'squid': '🦑',
    'bagel': '🥯', 'croissant': '🥐', 'baguette': '🥖', 'pretzel': '🥨',
    'pancake': '🥞', 'waffle': '🧇', 'donut': '🍩', 'muffin': '🧁',
    'honey': '🍯', 'jam': '🍯', 'peanut': '🥜', 'almond': '🌰',
    'yogurt': '🥛', 'cream': '🥛', 'tofu': '�豆腐', 'beans': '🫘'
}

updated = 0
skipped = 0

for item in items:
    user_id = item['userId']['S']
    item_id = item['itemId']['S']
    item_name = item.get('itemName', {}).get('S', '').lower()

    # Skip if already has emoji
    if 'emoji' in item:
        print(f"✓ Skipping {item_name} - already has emoji")
        skipped += 1
        continue

    # Find matching emoji
    emoji = '🛒'  # Default
    for key, value in EMOJI_MAP.items():
        if key in item_name:
            emoji = value
            break

    # Update DynamoDB
    try:
        dynamodb.update_item(
            TableName='ShoppingList',
            Key={
                'userId': {'S': user_id},
                'itemId': {'S': item_id}
            },
            UpdateExpression='SET emoji = :emoji',
            ExpressionAttributeValues={
                ':emoji': {'S': emoji}
            }
        )
        print(f"✓ Updated: {item_name} → {emoji}")
        updated += 1
    except Exception as e:
        print(f"✗ Error updating {item_name}: {e}")

print(f"\n✅ Backfill complete!")
print(f"   Updated: {updated} items")
print(f"   Skipped: {skipped} items")
print(f"   Total: {len(items)} items")
EOF

echo "Done!"
