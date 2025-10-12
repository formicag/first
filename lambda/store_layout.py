"""
Store layout configuration for shopping list ordering.

This defines the order of categories from store entrance (position 1)
to furthest from entrance (position 16).
"""

# Default store layout - Sainsbury's layout
# Position 1 = closest to entrance, Position 16 = furthest from entrance
DEFAULT_STORE_LAYOUT = {
    "Health & Beauty": 1,
    "Fresh Produce - Herbs & Salads": 2,
    "Fresh Produce - Fruit": 3,
    "Fresh Produce - Vegetables": 4,
    "Meat & Poultry": 5,
    "Household & Cleaning": 6,  # Office/Party/Home section
    "Dairy & Eggs": 8,
    "Beverages": 9,  # Chilled drinks (will handle both chilled and ambient)
    "Pantry & Dry Goods": 10,
    "Canned & Jarred": 11,
    "Bakery & Bread": 12,
    "Alcohol & Wine": 13,
    "Snacks & Confectionery": 14,
    "Frozen Foods": 16,
    "Fish & Seafood": 5,  # Typically near meat section
    "Baby & Child": 6,  # Typically in household section
    "Uncategorized": 99  # Always last
}

def get_category_position(category, custom_layout=None):
    """
    Get the position of a category in the store layout.

    Args:
        category: Category name
        custom_layout: Optional custom layout dict (overrides default)

    Returns:
        int: Position number (1 = entrance, higher = further back)
    """
    layout = custom_layout if custom_layout else DEFAULT_STORE_LAYOUT
    return layout.get(category, 99)  # Default to 99 (end) if not found


def sort_items_by_store_layout(items, custom_layout=None):
    """
    Sort shopping list items by store layout order.

    Items are sorted from entrance to back of store, then alphabetically
    within each category.

    Args:
        items: List of item dictionaries with 'category' and 'itemName' keys
        custom_layout: Optional custom layout dict

    Returns:
        list: Sorted list of items
    """
    return sorted(items, key=lambda item: (
        get_category_position(item.get('category', 'Uncategorized'), custom_layout),
        item.get('category', 'Uncategorized'),
        item.get('itemName', '')
    ))
