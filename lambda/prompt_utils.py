"""
Modular AI Prompt Builder for Shopping List Application

Provides reusable prompt templates for different AI tasks.
Makes it easy to maintain and update AI prompts in one place.
"""

import json
import os

# Bedrock model configuration - can be changed via environment variable
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL",
    "anthropic.claude-3-haiku-20240307-v1:0"
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


def build_item_processing_prompt(
    item_name,
    custom_prompt="",
    context_items=None,
    use_uk_english=True,
    strict_categories=True
):
    """
    Build a comprehensive prompt for processing a single grocery item.

    Tasks performed:
    - Spell checking and correction
    - Capitalization (first letter of each word)
    - Emoji assignment
    - Price estimation (Sainsbury's UK)
    - Category assignment (UK supermarket aisles)

    Args:
        item_name: Name of the grocery item
        custom_prompt: Optional custom instructions
        context_items: List of {term, meaning} for household-specific context
        use_uk_english: Whether to enforce UK English spelling
        strict_categories: Whether to strictly use predefined categories

    Returns:
        str: Complete prompt for AI processing
    """
    categories_str = ", ".join(UK_CATEGORIES)

    prompt = f"""You are a UK shopping assistant helping to process grocery items.

For this item: '{item_name}'"""

    # Add UK English instruction if enabled
    if use_uk_english:
        prompt += """

IMPORTANT: Use UK English spelling and terminology.
Examples: colour (not color), flavour (not flavor), courgette (not zucchini), aubergine (not eggplant)"""

    # Add household context if provided
    if context_items:
        prompt += "\n\nHOUSEHOLD CONTEXT (Gianluca and Nicole's specific meanings):\n"
        for item in context_items:
            prompt += f"- \"{item['term']}\" means {item['meaning']}\n"

    prompt += """

TASK 1 - Spelling Correction:
- Correct any spelling mistakes
- If spelling is already correct, keep the original name
- Ensure proper spacing

TASK 2 - Capitalization:
- Capitalize the FIRST letter of EACH word
- Examples: "pork chops" → "Pork Chops", "tomato" → "Tomato"

TASK 3 - Emoji Selection:
- Choose ONE emoji that best represents this item
- Use the most common, recognizable emoji for the item
- Examples: "Milk" → "🥛", "Bread" → "🍞", "Apples" → "🍎", "Chicken" → "🍗"

TASK 4 - Price Estimation:
- Estimate the typical price at Sainsbury's UK for this item
- Consider the quantity mentioned (if any) or assume standard pack size
- Return price in GBP (pounds) as a decimal number
- Examples: "Milk" → 1.25, "Bread" → 1.10, "Apples" (per kg) → 2.50
- Use typical 2024-2025 Sainsbury's pricing
- For unclear quantities, estimate for a typical single purchase unit
"""

    # Add categorization task
    if strict_categories:
        prompt += f"""
TASK 5 - Categorization:
- Categorize into ONE of these UK shopping centre aisles: {categories_str}
- Use standard UK supermarket terminology
- Think about where this would be found in a typical Tesco, Sainsbury's, or Asda"""
    else:
        prompt += f"""
TASK 5 - Categorization:
- Categorize into ONE of these UK shopping centre aisles: {categories_str}
- You may suggest alternative category names if more appropriate"""

    # Add custom prompt if provided
    if custom_prompt and custom_prompt.strip():
        prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt.strip()}"

    prompt += """\n\nReturn ONLY valid JSON in this exact format:
{"correctedName": "Item Name With Proper Capitalization", "emoji": "🥛", "estimatedPrice": 1.25, "category": "Category Name"}"""

    return prompt


def build_bulk_price_prompt(item_names):
    """
    Build prompt for bulk price estimation.

    Args:
        item_names: List of item names to price

    Returns:
        str: Prompt for bulk pricing
    """
    if not item_names:
        return ""

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

    return prompt


def build_categorization_prompt(items, custom_prompt=""):
    """
    Build prompt for bulk categorization.

    Args:
        items: List of item dictionaries with itemName
        custom_prompt: Optional custom instructions

    Returns:
        str: Prompt for bulk categorization
    """
    categories_str = ", ".join(UK_CATEGORIES)
    items_list = "\n".join([f"- {item.get('itemName', '')}" for item in items])

    prompt = f"""You are a UK grocery categorization assistant.

Categorize these items into UK supermarket aisles:

{items_list}

Available categories: {categories_str}

Use UK English and think about typical Tesco, Sainsbury's, or Asda layout.
"""

    if custom_prompt and custom_prompt.strip():
        prompt += f"\n\nAdditional instructions: {custom_prompt}"

    prompt += """\n\nReturn a JSON array with objects containing itemName and category:
[{"itemName": "Milk", "category": "Dairy & Eggs"}]"""

    return prompt


def get_bedrock_model_id():
    """
    Get the configured Bedrock model ID.

    Returns:
        str: Bedrock model identifier
    """
    return BEDROCK_MODEL_ID


def get_uk_categories():
    """
    Get the list of UK supermarket categories.

    Returns:
        list: UK shopping centre categories
    """
    return UK_CATEGORIES.copy()
