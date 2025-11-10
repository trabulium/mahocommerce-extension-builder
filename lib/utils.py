"""
Utility functions for MahoCommerce module generation.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""

import os
from pathlib import Path


def get_code_pool(namespace: str) -> str:
    """
    Determine the appropriate code pool for a namespace

    Args:
        namespace: Module namespace (e.g., 'Maho', 'Custom')

    Returns:
        Code pool name ('core', 'community', or 'local')
    """
    if namespace == 'Maho' or namespace == 'Mage':
        return 'core'
    elif namespace in ['Custom', 'Local']:
        return 'local'
    else:
        return 'community'


def check_conflicts(namespace: str, module_name: str, base_path: str = None) -> list:
    """
    Check if module files would conflict with existing files

    Args:
        namespace: Module namespace
        module_name: Module name
        base_path: Base path to check (defaults to current directory + '../../../')

    Returns:
        List of conflicting file paths (empty list if no conflicts)
    """
    if base_path is None:
        # Default to going up 3 directories from the skill directory
        base_path = Path(__file__).parent.parent.parent.parent.parent

    base_path = Path(base_path)
    code_pool = get_code_pool(namespace)

    conflicts = []

    # Check module declaration
    module_xml = base_path / 'app' / 'etc' / 'modules' / f'{namespace}_{module_name}.xml'
    if module_xml.exists():
        conflicts.append(str(module_xml))

    # Check module directory
    module_dir = base_path / 'app' / 'code' / code_pool / namespace / module_name
    if module_dir.exists():
        conflicts.append(str(module_dir))

    return conflicts


def ensure_dir(file_path: str) -> None:
    """
    Ensure directory exists for a file path

    Args:
        file_path: File path to ensure directory for
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def write_file(file_path: str, content: str) -> None:
    """
    Write content to a file, creating directories as needed

    Args:
        file_path: Path to write to
        content: Content to write
    """
    ensure_dir(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def to_snake_case(text: str) -> str:
    """
    Convert text to snake_case

    Args:
        text: Text to convert

    Returns:
        snake_case version
    """
    import re
    # Insert underscore before uppercase letters and convert to lowercase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(text: str) -> str:
    """
    Convert text to CamelCase

    Args:
        text: Text to convert (can be snake_case or space-separated)

    Returns:
        CamelCase version
    """
    # Split on underscores or spaces
    parts = text.replace('_', ' ').split()
    return ''.join(word.capitalize() for word in parts)


def get_table_name(namespace: str, module_name: str, entity_name: str) -> str:
    """
    Generate standard table name for an entity

    Args:
        namespace: Module namespace
        module_name: Module name
        entity_name: Entity name

    Returns:
        Table name in format: namespace_modulename_entityname
    """
    return f'{namespace.lower()}_{to_snake_case(module_name)}_{to_snake_case(entity_name)}'
