"""
Configuration validation and defaults for MahoCommerce module generation.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""

from lib.utils import to_snake_case, to_camel_case


def apply_defaults(config: dict) -> dict:
    """
    Apply default values to module configuration

    Args:
        config: Module configuration dictionary

    Returns:
        Configuration with defaults applied
    """
    # Set default namespace
    if 'namespace' not in config:
        config['namespace'] = 'Maho'

    # Set default version
    if 'version' not in config:
        config['version'] = '24.11.0'

    # Process entities
    if 'entities' in config:
        for entity in config['entities']:
            # Set default label from name
            if 'label' not in entity:
                entity['label'] = entity['name'].replace('_', ' ').title()

            # Set default table name
            if 'table' not in entity:
                entity['table'] = to_snake_case(entity['name'])

            # Ensure fields exist
            if 'fields' not in entity:
                entity['fields'] = []

            # Process field defaults
            for field in entity['fields']:
                # Set default type
                if 'type' not in field:
                    field['type'] = 'varchar'

                # Set default nullable
                if 'nullable' not in field:
                    field['nullable'] = True

                # Set default label from name
                if 'label' not in field:
                    field['label'] = field['name'].replace('_', ' ').title()

                # Set VARCHAR default length
                if field['type'] in ['varchar', 'text'] and 'length' not in field:
                    if field['type'] == 'varchar':
                        field['length'] = 255

                # Set default admin display settings
                if 'admin' not in field:
                    field['admin'] = {}

                if 'grid' not in field['admin']:
                    # Show in grid by default for key fields
                    field['admin']['grid'] = field['name'] in ['name', 'title', 'status', 'created_at']

                if 'form' not in field['admin']:
                    # Show in form by default (except ID and timestamps)
                    field['admin']['form'] = field['name'] not in ['created_at', 'updated_at']

            # Set default admin settings
            if 'admin' not in entity:
                entity['admin'] = {}

            if 'menu' not in entity['admin']:
                entity['admin']['menu'] = True

            if 'acl' not in entity['admin']:
                entity['admin']['acl'] = True

            # Set default frontend settings
            if 'frontend' not in entity:
                entity['frontend'] = {}

            if 'enabled' not in entity['frontend']:
                entity['frontend']['enabled'] = False

            # Auto-enable multi_store for frontend entities
            if entity['frontend']['enabled'] and 'multi_store' not in entity:
                entity['multi_store'] = True

            # Process relationships
            if 'relationships' in entity:
                for rel in entity['relationships']:
                    # Set relationship type default
                    if 'type' not in rel:
                        rel['type'] = 'many_to_many'

                    # Set junction table name for many-to-many
                    if rel['type'] == 'many_to_many' and 'junction_table' not in rel:
                        entity_table = entity.get('table', to_snake_case(entity['name']))
                        target_table = to_snake_case(rel['target'])
                        # Alphabetically order the tables for consistency
                        tables = sorted([entity_table, target_table])
                        rel['junction_table'] = f"{tables[0]}_{tables[1]}"

    return config


def validate_config(config: dict) -> tuple[bool, list]:
    """
    Validate module configuration

    Args:
        config: Module configuration dictionary

    Returns:
        Tuple of (is_valid: bool, errors: list)
    """
    errors = []

    # Validate required top-level fields
    if 'name' not in config:
        errors.append("Missing required field: 'name'")

    if 'namespace' not in config:
        errors.append("Missing required field: 'namespace'")

    # Validate entities
    if 'entities' not in config or not config['entities']:
        errors.append("Module must have at least one entity")
    else:
        for idx, entity in enumerate(config['entities']):
            entity_ref = f"Entity {idx} ('{entity.get('name', 'unnamed')}')"

            # Validate entity name
            if 'name' not in entity:
                errors.append(f"{entity_ref}: Missing required field 'name'")

            # Validate fields
            if 'fields' not in entity or not entity['fields']:
                errors.append(f"{entity_ref}: Must have at least one field")
            else:
                for field_idx, field in enumerate(entity['fields']):
                    field_ref = f"{entity_ref}, Field {field_idx}"

                    if 'name' not in field:
                        errors.append(f"{field_ref}: Missing required field 'name'")

                    # Validate field types
                    valid_types = [
                        'int', 'smallint', 'bigint', 'tinyint',
                        'varchar', 'text', 'mediumtext', 'longtext',
                        'decimal', 'float', 'double',
                        'datetime', 'date', 'timestamp',
                        'boolean', 'bool'
                    ]
                    if 'type' in field and field['type'] not in valid_types:
                        errors.append(f"{field_ref}: Invalid type '{field['type']}'. Valid types: {', '.join(valid_types)}")

            # Validate relationships
            if 'relationships' in entity:
                for rel_idx, rel in enumerate(entity['relationships']):
                    rel_ref = f"{entity_ref}, Relationship {rel_idx}"

                    if 'target' not in rel:
                        errors.append(f"{rel_ref}: Missing required field 'target'")

                    if 'type' in rel and rel['type'] not in ['one_to_many', 'many_to_many']:
                        errors.append(f"{rel_ref}: Invalid type '{rel['type']}'. Valid types: one_to_many, many_to_many")

    return (len(errors) == 0, errors)
