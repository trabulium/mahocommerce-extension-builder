"""
Field utilities for MahoCommerce module generator.

Handles field normalization, type synonyms, labels, and visibility.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""


# Type synonyms mapping
TYPE_ALIASES = {
    'tinyint': 'smallint',
    'timestamp': 'datetime',
    'boolean': 'bool',
    'string': 'varchar',
}


def normalize_field_type(field_type):
    """
    Normalize field type using type synonyms.

    Args:
        field_type: Raw field type from config

    Returns:
        Normalized field type
    """
    return TYPE_ALIASES.get(field_type.lower(), field_type.lower())


def get_field_label(field):
    """
    Get user-friendly label for a field.
    Falls back to auto-generated label if not specified.

    Args:
        field: Field dict with 'name' and optional 'label'

    Returns:
        User-friendly label string
    """
    if 'label' in field:
        return field['label']

    # Auto-generate from field name
    field_name = field['name']

    # Special cases for common abbreviations
    special_cases = {
        'url_key': 'SEO URL Key',
        'seo_title': 'SEO Title',
        'meta_description': 'Meta Description',
        'meta_keywords': 'Meta Keywords',
        'api_key': 'API Key',
        'ip_address': 'IP Address',
        'id': 'ID',
    }

    if field_name in special_cases:
        return special_cases[field_name]

    # Convert snake_case to Title Case
    # Keep common abbreviations uppercase
    words = field_name.replace('_', ' ').split()
    title_words = []

    for word in words:
        # Keep certain abbreviations uppercase
        if word.lower() in ['id', 'url', 'seo', 'api', 'ip', 'xml', 'json', 'html', 'css', 'js']:
            title_words.append(word.upper())
        else:
            title_words.append(word.capitalize())

    return ' '.join(title_words)


def is_field_required(field):
    """
    Determine if a field is required (NOT NULL).
    Supports both 'required' and 'nullable' syntax.

    Args:
        field: Field dict with optional 'required' or 'nullable' keys

    Returns:
        True if field is required (NOT NULL), False otherwise
    """
    # If 'required' is explicitly set, use that
    if 'required' in field:
        return field['required']

    # If 'nullable' is set, invert it
    if 'nullable' in field:
        return not field['nullable']

    # Default: fields are nullable unless specified otherwise
    return False


def should_show_in_grid(field):
    """
    Determine if field should appear in admin grid.
    Supports explicit admin.grid config or auto-detection.

    Args:
        field: Field dict with optional 'admin': {'grid': bool}

    Returns:
        True if field should appear in grid
    """
    # Check for explicit setting
    admin_config = field.get('admin', {})
    if 'grid' in admin_config:
        return admin_config['grid']

    # Auto-detect based on field characteristics
    field_name = field['name']
    field_type = normalize_field_type(field.get('type', 'varchar'))

    # Always show ID, title/name fields
    if field_name in ['name', 'title', 'email']:
        return True

    # Show relationship fields (author_id, category_id, etc.)
    if field_name.endswith('_id') and field_name not in ['entity_id']:
        return True

    # Show boolean flags (is_active, is_published, etc.)
    if field_name.startswith('is_') or field_name.startswith('allow_'):
        return True

    # Show status field
    if field_name == 'status':
        return True

    # Don't show large text fields
    if field_type in ['text', 'longtext', 'mediumtext']:
        return False

    # Don't show meta fields
    if field_name.startswith('meta_'):
        return False

    # Don't show content/body fields
    if field_name in ['content', 'body', 'description', 'bio']:
        return False

    # Show short fields (varchar) but not long ones
    if field_type == 'varchar':
        length = field.get('length', 255)
        return length <= 255

    # Show numeric fields
    if field_type in ['int', 'smallint', 'decimal']:
        return True

    # Show dates
    if field_type in ['datetime', 'date']:
        return True

    # Default: don't show
    return False


def should_show_in_form(field):
    """
    Determine if field should appear in admin form.
    Supports explicit admin.form config or auto-detection.

    Args:
        field: Field dict with optional 'admin': {'form': bool}

    Returns:
        True if field should appear in form
    """
    # Check for explicit setting
    admin_config = field.get('admin', {})
    if 'form' in admin_config:
        return admin_config['form']

    # Auto-detect: show all fields except entity_id in forms
    field_name = field['name']

    # Don't show auto-generated IDs
    if field_name.endswith('_id') and field_name != 'entity_id':
        # Foreign keys SHOULD show in forms as dropdowns
        return True

    if field_name == 'entity_id':
        return False

    # Don't show timestamp fields (auto-managed)
    if field_name in ['created_at', 'updated_at']:
        return False

    # Show everything else
    return True


def get_grid_columns(fields, entity_name):
    """
    Get list of fields that should appear as columns in grid.

    Args:
        fields: List of field dicts
        entity_name: Entity name (for ID column)

    Returns:
        List of field dicts that should be grid columns
    """
    # Always include ID first
    grid_fields = [{'name': entity_name + '_id', 'type': 'int', 'label': 'ID'}]

    # Add user-defined fields that should show in grid
    for field in fields:
        if should_show_in_grid(field):
            grid_fields.append(field)

    # Always include status, created_at at end if they exist
    field_names = [f['name'] for f in fields]

    if 'status' in field_names and not any(f['name'] == 'status' for f in grid_fields):
        status_field = next(f for f in fields if f['name'] == 'status')
        grid_fields.append(status_field)

    if 'created_at' in field_names:
        created_field = next(f for f in fields if f['name'] == 'created_at')
        if not any(f['name'] == 'created_at' for f in grid_fields):
            grid_fields.append(created_field)

    return grid_fields


def get_form_fields(fields):
    """
    Get list of fields that should appear in form.

    Args:
        fields: List of field dicts

    Returns:
        List of field dicts that should be in form
    """
    return [f for f in fields if should_show_in_form(f)]
