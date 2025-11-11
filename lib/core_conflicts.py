"""
Core Module Conflict Detection

Detects when entity names conflict with Mage's built-in modules.
"""

# Entity names that conflict with core Mage modules
# These will cause layout handle conflicts when used as entity names
RESERVED_ENTITY_NAMES = {
    'tag': 'Mage_Tag - Product tagging system',
    'review': 'Mage_Review - Product reviews',
    'rating': 'Mage_Rating - Product ratings',
    'poll': 'Mage_Poll - Customer polls',
    'wishlist': 'Mage_Wishlist - Customer wishlists',
    'newsletter': 'Mage_Newsletter - Newsletter subscriptions',
    'customer': 'Mage_Customer - Customer accounts',
    'product': 'Mage_Catalog - Product catalog',
    'category': 'Mage_Catalog - Category management (may conflict)',
    'order': 'Mage_Sales - Order management',
    'invoice': 'Mage_Sales - Invoices',
    'shipment': 'Mage_Sales - Shipments',
    'cms': 'Mage_Cms - CMS pages/blocks',
    'widget': 'Mage_Widget - CMS widgets',
    'report': 'Mage_Reports - Reporting system',
}


def check_entity_conflicts(entities):
    """
    Check if any entity names conflict with core Mage modules.

    Args:
        entities: List of entity dictionaries with 'name' key

    Returns:
        List of conflict warnings
    """
    conflicts = []

    for entity in entities:
        entity_name = entity.get('name', '').lower()

        if entity_name in RESERVED_ENTITY_NAMES:
            module_info = RESERVED_ENTITY_NAMES[entity_name]
            conflicts.append({
                'entity': entity_name,
                'module': module_info,
                'severity': 'high' if entity_name in ['tag', 'review', 'rating', 'poll'] else 'medium'
            })

    return conflicts


def format_conflict_warning(conflicts):
    """
    Format conflict warnings for display.

    Args:
        conflicts: List of conflict dictionaries

    Returns:
        Formatted warning string
    """
    if not conflicts:
        return None

    warning = "\n⚠️  ENTITY NAME CONFLICTS DETECTED:\n\n"

    for conflict in conflicts:
        severity_icon = "🔴" if conflict['severity'] == 'high' else "🟡"
        warning += f"{severity_icon} Entity '{conflict['entity']}' conflicts with {conflict['module']}\n"

    warning += "\n💡 RECOMMENDATIONS:\n"
    warning += "   1. Rename conflicting entities (e.g., 'blog_tag' instead of 'tag')\n"
    warning += "   2. This will cause layout handle conflicts and duplicate admin grids\n"
    warning += "   3. Core module routes will take precedence over your custom entities\n"
    warning += "\nContinue anyway? This may cause issues in the admin interface.\n"

    return warning
