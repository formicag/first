#!/usr/bin/env python3
"""
Simple script to add emojis to existing items using a mapping.
Run with: python3 simple_backfill.py
"""

import subprocess
import json

# Simple emoji mapping
EMOJI_MAP = {
    'milk': '🥛', 'bread': '🍞', 'rye bread': '🍞', 'eggs': '🥚', 'cheese': '🧀',
    'butter': '🧈', 'apple': '🍎', 'banana': '🍌', 'orange': '🍊',
    'tomato': '🍅', 'potato': '🥔', 'carrot': '🥕', 'onion': '🧅',
    'chicken': '🍗', 'beef': '🥩', 'fish': '🐟', 'bacon': '🥓',
    'pasta': '🍝', 'rice': '🍚', 'pizza': '🍕', 'sandwich': '🥪',
    'salad': '🥗', 'soup': '🍲', 'coffee': '☕', 'tea': '🍵',
    'water': '💧', 'juice': '🧃', 'wine': '🍷', 'beer': '🍺',
    'chocolate': '🍫', 'cookie': '🍪', 'cake': '🍰', 'ice cream': '🍦',
    'strawberry': '🍓', 'grape': '🍇', 'watermelon': '🍉', 'lemon': '🍋',
    'avocado': '🥑', 'broccoli': '🥦', 'mushroom': '🍄', 'corn': '🌽',
    'pepper': '🌶️', 'garlic': '🧄', 'cucumber': '🥒',
    'peanut butter': '🥜', 'jam': '🍯', 'honey': '🍯',
    'yogurt': '🥛', 'cream': '🥛',
    'bounty': '🍫', 'chocolate bar': '🍫',
    'dishwasher': '🧼', 'tablets': '🧼', 'dishwasher tablets': '🧼',
    'soap': '🧼', 'detergent': '🧼', 'cleaner': '🧴',
    'kombucha': '🍵', 'kambucha': '🍵', 'sparkling': '🥤',
    'crisps': '🥔', 'chips': '🍟', 'snack': '🍿',
    'nuts': '🥜', 'almonds': '🌰', 'cashews': '🥜',
    'meat': '🥩', 'steak': '🥩', 'sausage': '🌭',
    'vegetables': '🥬', 'fruit': '🍎', 'berries': '🫐'
}

def get_emoji(item_name):
    """Find best matching emoji for an item name."""
    item_lower = item_name.lower()

    # Try exact match first
    if item_lower in EMOJI_MAP:
        return EMOJI_MAP[item_lower]

    # Try partial matches
    for key, emoji in EMOJI_MAP.items():
        if key in item_lower:
            return emoji

    # Default
    return '🛒'

def main():
    print("🔄 Starting emoji backfill...")

    # Get all items
    result = subprocess.run([
        'aws', 'dynamodb', 'scan',
        '--table-name', 'ShoppingList',
        '--region', 'eu-west-1',
        '--output', 'json'
    ], capture_output=True, text=True)

    data = json.loads(result.stdout)
    items = data['Items']

    print(f"📊 Found {len(items)} total items")

    updated = 0
    skipped = 0

    for item in items:
        user_id = item['userId']['S']
        item_id = item['itemId']['S']
        item_name = item['itemName']['S']

        # Skip if already has emoji
        if 'emoji' in item:
            print(f"⏭️  Skipping {item_name} - already has emoji {item['emoji']['S']}")
            skipped += 1
            continue

        # Get emoji
        emoji = get_emoji(item_name)

        # Update DynamoDB
        subprocess.run([
            'aws', 'dynamodb', 'update-item',
            '--table-name', 'ShoppingList',
            '--region', 'eu-west-1',
            '--key', json.dumps({'userId': {'S': user_id}, 'itemId': {'S': item_id}}),
            '--update-expression', 'SET emoji = :emoji',
            '--expression-attribute-values', json.dumps({':emoji': {'S': emoji}})
        ], capture_output=True)

        print(f"✅ Updated: {emoji} {item_name}")
        updated += 1

    print(f"\n🎉 Backfill complete!")
    print(f"   ✅ Updated: {updated} items")
    print(f"   ⏭️  Skipped: {skipped} items")
    print(f"   📊 Total: {len(items)} items")

if __name__ == '__main__':
    main()
