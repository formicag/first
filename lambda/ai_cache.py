"""
AI Cache Layer for Shopping List Application

Caches AI results to reduce Bedrock API calls and costs.
Results are cached by item name hash for fast retrieval.
"""

import boto3
import hashlib
import json
import os
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cache table name from environment
CACHE_TABLE = os.environ.get("AI_CACHE_TABLE", "ShoppingList-AICache-Dev")

dynamodb = boto3.resource("dynamodb")

def _get_cache_table():
    """Get cache table reference with error handling."""
    try:
        return dynamodb.Table(CACHE_TABLE)
    except Exception as e:
        logger.warning(f"Cache table not available: {e}")
        return None

def _hash_key(item_name):
    """
    Generate a stable hash for an item name.
    Normalizes to lowercase and strips whitespace for consistency.
    """
    normalized = str(item_name).lower().strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def get_cached_result(item_name):
    """
    Return cached AI result if it exists.

    Args:
        item_name: Name of the item to look up

    Returns:
        dict or None: Cached result with correctedName, emoji, estimatedPrice, category
    """
    table = _get_cache_table()
    if not table:
        return None

    try:
        cache_key = _hash_key(item_name)
        response = table.get_item(Key={"cacheKey": cache_key})

        if "Item" in response:
            cached = response["Item"]
            logger.info(f"Cache HIT for '{item_name}'")

            # Return the result, converting Decimal to float for prices
            result = cached.get("result", {})
            if "estimatedPrice" in result:
                result["estimatedPrice"] = float(result["estimatedPrice"])
            return result
        else:
            logger.info(f"Cache MISS for '{item_name}'")
            return None

    except Exception as e:
        logger.error(f"Error reading from cache: {e}")
        return None

def save_cached_result(item_name, result):
    """
    Save AI result to cache.

    Args:
        item_name: Name of the item
        result: dict with correctedName, emoji, estimatedPrice, category
    """
    table = _get_cache_table()
    if not table:
        return

    try:
        cache_key = _hash_key(item_name)

        # Convert float prices to Decimal for DynamoDB
        cache_result = result.copy()
        if "estimatedPrice" in cache_result:
            cache_result["estimatedPrice"] = Decimal(str(cache_result["estimatedPrice"]))

        table.put_item(Item={
            "cacheKey": cache_key,
            "itemName": item_name.lower().strip(),  # Store normalized name for reference
            "result": cache_result,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ttl": int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)  # 30 day TTL
        })
        logger.info(f"Cached result for '{item_name}'")

    except Exception as e:
        logger.error(f"Error saving to cache: {e}")

def clear_cache_for_item(item_name):
    """
    Clear cached result for a specific item.
    Useful if prices need to be refreshed.

    Args:
        item_name: Name of the item to clear from cache
    """
    table = _get_cache_table()
    if not table:
        return

    try:
        cache_key = _hash_key(item_name)
        table.delete_item(Key={"cacheKey": cache_key})
        logger.info(f"Cleared cache for '{item_name}'")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
