#!/usr/bin/env python3
"""
Maho Module Generator

Generates a complete, working Maho module from a declarative config.
Based on proven working patterns - no guessing, just mechanical generation.

Usage:
    python generate-module.py config.json
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import yaml

# Import modular generators
from lib.admin_generator import (
    generate_admin_controller,
    generate_admin_blocks,
    generate_adminhtml_layout_handles
)
from lib.frontend_generator import (
    generate_frontend_controller,
    generate_related_entity_controllers,
    generate_frontend_blocks,
    generate_frontend_templates,
    generate_frontend_layout_handles,
    generate_sidebar_blocks
)
from lib.model_generator import generate_model_files
from lib.templates.core import module_declaration, helper_class, adminhtml_xml
from lib.config import validate_config, apply_defaults
from lib.utils import check_conflicts as lib_check_conflicts, get_code_pool
from lib.system_config_generator import (
    present_system_config_suggestions,
    generate_system_xml
)
from lib.url_rewrite_generator import (
    has_url_key_field,
    generate_url_rewrite_observer,
    add_url_rewrite_events
)

def check_frontend_route_conflict(front_name):
    """Check if a frontend route already exists"""
    conflicts = []

    # Check app/code and vendor for existing frontName routes
    search_paths = [
        'app/code',
        'vendor/mahocommerce/maho/app/code'
    ]

    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue

        for root, dirs, files in os.walk(base_path):
            if 'config.xml' in files:
                config_file = os.path.join(root, 'config.xml')
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if f'<frontName>{front_name}</frontName>' in content:
                            # Extract module name from path
                            module_match = re.search(r'/([^/]+/[^/]+)/etc/config\.xml', config_file)
                            if module_match:
                                conflicts.append({
                                    'module': module_match.group(1),
                                    'file': config_file
                                })
                except:
                    pass

    return conflicts


def detect_relationships(entities):
    """
    Auto-detect relationships between entities based on common patterns.
    Returns list of relationship definitions: [(entity1, entity2), ...]
    """
    relationships = []
    entity_names = [e['name'].lower() for e in entities]

    # Common relationship patterns
    main_entities = ['post', 'product', 'item', 'article']
    related_entities = ['category', 'tag', 'author']

    for main in main_entities:
        if main in entity_names:
            for related in related_entities:
                if related in entity_names:
                    # Skip author as it's usually a foreign key, not many-to-many
                    if related != 'author':
                        relationships.append((main, related))

    return relationships

def generate_module(config):
    """Generate a complete Maho module from config"""

    namespace = config['namespace']
    module = config['module']
    entities = config.get('entities', [])
    year = datetime.now().year

    print(f"Generating module: {namespace}_{module}")
    print(f"Entities: {', '.join([e['name'] for e in entities])}")

    # Check for conflicts
    print("\n[CHECK] Checking for conflicts...")
    conflicts = lib_check_conflicts(namespace, module)
    if conflicts:
        print("\n❌ CONFLICTS DETECTED:\n")
        for conflict in conflicts:
            print(conflict)
        print("\n💡 RECOMMENDATIONS:")
        print(f"   1. Use a custom namespace (e.g., 'Custom_{module}' instead of '{namespace}_{module}')")
        print(f"   2. Choose a different module name")
        print(f"   3. Remove the existing module if you want to replace it")
        print("\nGeneration aborted to prevent conflicts.")
        sys.exit(1)
    print("  ✓ No conflicts found")

    # Check for frontend route conflicts
    default_front_name = module.lower()
    front_name = config.get('frontend_route', default_front_name)

    route_conflicts = check_frontend_route_conflict(front_name)
    if route_conflicts:
        print(f"\n⚠️  WARNING: Frontend route '{front_name}' is already in use by:")
        for conflict in route_conflicts:
            print(f"   - {conflict['module']}")

        # Check if we're in interactive mode
        import sys
        is_interactive = sys.stdin.isatty()

        if is_interactive:
            # Prompt for alternative
            while True:
                try:
                    alt_route = input(f"\nEnter alternative frontend route (or press Enter to skip frontend): ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n  ⓘ Skipping frontend route generation")
                    config['skip_frontend'] = True
                    break

                if not alt_route:
                    print("  ⓘ Skipping frontend route generation")
                    config['skip_frontend'] = True
                    break
                elif check_frontend_route_conflict(alt_route):
                    print(f"  ✗ '{alt_route}' is also taken, try another")
                else:
                    print(f"  ✓ Using '{alt_route}' as frontend route")
                    config['frontend_route'] = alt_route
                    front_name = alt_route
                    break
        else:
            # Non-interactive mode - abort if not provided in config
            print(f"\n❌ ERROR: Frontend route conflict detected in non-interactive mode")
            print(f"   Please specify 'frontend_route' in your config JSON with a unique route name")
            print(f"   Example: \"frontend_route\": \"{module.lower()}-blog\"")
            sys.exit(1)
    else:
        print(f"  ✓ Frontend route '{front_name}' available")
        config['frontend_route'] = front_name

    # Base paths - use 'local' for custom modules, 'core' for Maho/Mage namespace
    code_pool = get_code_pool(namespace)
    code_path = Path(f"app/code/{code_pool}/{namespace}/{module}")
    etc_path = code_path / "etc"
    controllers_path = code_path / "controllers"
    blocks_path = code_path / "Block"
    models_path = code_path / "Model"
    helpers_path = code_path / "Helper"
    sql_path = code_path / "sql" / f"{namespace.lower()}_{module.lower()}_setup"

    adminhtml_design_path = Path(f"app/design/adminhtml/default/default")
    adminhtml_layout_path = adminhtml_design_path / "layout" / namespace.lower() / f"{module.lower()}.xml"

    frontend_design_path = Path(f"app/design/frontend/base/default")
    frontend_layout_path = frontend_design_path / "layout" / namespace.lower() / f"{module.lower()}.xml"

    module_decl_path = Path(f"app/etc/modules/{namespace}_{module}.xml")

    files_created = []

    # 1. Module Declaration
    print("\n[1] Creating module declaration...")
    module_decl_path.parent.mkdir(parents=True, exist_ok=True)
    module_decl = f"""<?xml version="1.0"?>
<!--
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 * @license    https://opensource.org/licenses/OSL-3.0 Open Software License v. 3.0 (OSL-3.0)
 */
-->
<config>
    <modules>
        <{namespace}_{module}>
            <active>true</active>
            <codePool>{code_pool}</codePool>
            <depends>
                <Mage_Core/>
                <Mage_Adminhtml/>
            </depends>
        </{namespace}_{module}>
    </modules>
</config>
"""
    module_decl_path.write_text(module_decl)
    files_created.append(str(module_decl_path))

    # 2. config.xml
    print("[2] Creating config.xml...")
    etc_path.mkdir(parents=True, exist_ok=True)

    menu_items = ""
    acl_items = ""
    model_entities = ""

    for i, entity in enumerate(entities):
        entity_name = entity['name'].lower()
        entity_title = entity.get('title', entity['name'].replace('_', ' ').title())
        entity_label = entity.get('label', f"Manage {entity_title}")
        sort_order = (i + 1) * 10

        menu_items += f"""                    <{entity_name} translate="title">
                        <title>{entity_label}</title>
                        <action>adminhtml/{entity_name}/index</action>
                        <sort_order>{sort_order}</sort_order>
                    </{entity_name}>
"""

        acl_items += f"""                            <{entity_name} translate="title">
                                <title>{entity_title}</title>
                                <sort_order>{sort_order}</sort_order>
                            </{entity_name}>
"""

        model_entities += f"""                    <{entity_name}>
                        <table>{namespace.lower()}_{module.lower()}_{entity_name}</table>
                    </{entity_name}>
"""

        # Add store junction table entity if multi_store is enabled
        if entity.get('multi_store', False):
            model_entities += f"""                    <{entity_name}_store>
                        <table>{namespace.lower()}_{module.lower()}_{entity_name}_store</table>
                    </{entity_name}_store>
"""

    # Get relationships from config or auto-detect
    config_relationships = config.get('relationships', [])
    if config_relationships:
        # Convert JSON relationships to tuple format: [{"entity1": "Recipe", "entity2": "Category", "type": "many_to_many"}]
        relationships = [(rel['entity1'].lower(), rel['entity2'].lower()) for rel in config_relationships if rel.get('type') == 'many_to_many']
        if relationships:
            print(f"\n[CONFIG] Found {len(relationships)} many-to-many relationships:")
            for rel in relationships:
                print(f"  - {rel[0]} ↔ {rel[1]}")
    else:
        # Fall back to auto-detection
        relationships = detect_relationships(entities)
        if relationships:
            print(f"\n[AUTO-DETECT] Found {len(relationships)} relationships:")
            for rel in relationships:
                print(f"  - {rel[0]} ↔ {rel[1]}")

    # Add relationship tables to config.xml
    if relationships:
        for rel in relationships:
            rel_table_name = f"{rel[0]}_{rel[1]}"
            model_entities += f"""                    <{rel_table_name}>
                        <table>{namespace.lower()}_{module.lower()}_{rel_table_name}</table>
                    </{rel_table_name}>
"""

    # Check for entities with url_key field for URL rewrite support
    # Main entity (first entity) automatically gets url_key for SEO URLs
    url_rewrite_events = ""
    entities_with_url_key = []
    for idx, entity in enumerate(entities):
        if has_url_key_field(entity.get('fields', [])) or idx == 0:
            entities_with_url_key.append(entity)

    if entities_with_url_key:
        print(f"\n[AUTO-DETECT] Found {len(entities_with_url_key)} entities with url_key for SEO URLs:")
        for entity in entities_with_url_key:
            print(f"  - {entity['name']}")

        # Only generate events for the primary entity (first one found)
        primary_entity = entities_with_url_key[0]
        entity_name = primary_entity['name']
        entity_class = entity_name.capitalize()
        url_rewrite_events += add_url_rewrite_events(namespace, module, entity_name, entity_class)

    config_xml = f"""<?xml version="1.0"?>
<config>
    <modules>
        <{namespace}_{module}>
            <version>1.0.0</version>
        </{namespace}_{module}>
    </modules>

    <global>
        <models>
            <{namespace.lower()}_{module.lower()}>
                <class>{namespace}_{module}_Model</class>
                <resourceModel>{namespace.lower()}_{module.lower()}_resource</resourceModel>
            </{namespace.lower()}_{module.lower()}>
            <{namespace.lower()}_{module.lower()}_resource>
                <class>{namespace}_{module}_Model_Resource</class>
                <entities>
{model_entities}                </entities>
            </{namespace.lower()}_{module.lower()}_resource>
        </models>

        <resources>
            <{namespace.lower()}_{module.lower()}_setup>
                <setup>
                    <module>{namespace}_{module}</module>
                </setup>
            </{namespace.lower()}_{module.lower()}_setup>
        </resources>

        <blocks>
            <{namespace.lower()}_{module.lower()}>
                <class>{namespace}_{module}_Block</class>
            </{namespace.lower()}_{module.lower()}>
        </blocks>

        <helpers>
            <{namespace.lower()}_{module.lower()}>
                <class>{namespace}_{module}_Helper</class>
            </{namespace.lower()}_{module.lower()}>
        </helpers>
{url_rewrite_events}    </global>

    <admin>
        <routers>
            <adminhtml>
                <args>
                    <modules>
                        <{namespace.lower()}_{module.lower()} before="Mage_Adminhtml">{namespace}_{module}_Adminhtml</{namespace.lower()}_{module.lower()}>
                    </modules>
                </args>
            </adminhtml>
        </routers>
    </admin>

    <frontend>
        <routers>
            <{namespace.lower()}_{module.lower()}>
                <use>standard</use>
                <args>
                    <module>{namespace}_{module}</module>
                    <frontName>{config.get('frontend_route', module.lower())}</frontName>
                </args>
            </{namespace.lower()}_{module.lower()}>
        </routers>
        <layout>
            <updates>
                <{namespace.lower()}_{module.lower()}>
                    <file>{namespace.lower()}/{module.lower()}.xml</file>
                </{namespace.lower()}_{module.lower()}>
            </updates>
        </layout>
    </frontend>

    <adminhtml>
        <layout>
            <updates>
                <{namespace.lower()}_{module.lower()}>
                    <file>{namespace.lower()}/{module.lower()}.xml</file>
                </{namespace.lower()}_{module.lower()}>
            </updates>
        </layout>

        <menu>
            <{namespace.lower()}_{module.lower()} translate="title">
                <title>{config.get('menu_title', module)}</title>
                <sort_order>{config.get('menu_sort', 80)}</sort_order>
                <children>
{menu_items}                </children>
            </{namespace.lower()}_{module.lower()}>
        </menu>
    </adminhtml>
</config>
"""
    (etc_path / "config.xml").write_text(config_xml)
    files_created.append(str(etc_path / "config.xml"))

    # 3. adminhtml.xml (ACL)
    print("[3] Creating adminhtml.xml...")

    # Add system config to ACL if we're generating it
    system_config_acl = ""
    if not config.get('skip_system_config', False):
        system_config_acl = f"""
                    <system>
                        <children>
                            <config>
                                <children>
                                    <{namespace.lower()}_{module.lower()} translate="title">
                                        <title>{module}</title>
                                    </{namespace.lower()}_{module.lower()}>
                                </children>
                            </config>
                        </children>
                    </system>"""

    adminhtml_xml = f"""<?xml version="1.0"?>
<config>
    <acl>
        <resources>
            <admin>
                <children>
                    <{namespace.lower()}_{module.lower()} translate="title">
                        <title>{config.get('menu_title', module)}</title>
                        <sort_order>{config.get('menu_sort', 80)}</sort_order>
                        <children>
{acl_items}                        </children>
                    </{namespace.lower()}_{module.lower()}>{system_config_acl}
                </children>
            </admin>
        </resources>
    </acl>
</config>
"""
    (etc_path / "adminhtml.xml").write_text(adminhtml_xml)
    files_created.append(str(etc_path / "adminhtml.xml"))

    # 3.5. System Configuration
    if not config.get('skip_system_config', False):
        system_config_groups = present_system_config_suggestions(namespace, module, entities)
        if system_config_groups:
            print("[3.5] Creating system.xml...")
            generate_system_xml(namespace, module, system_config_groups, code_path, files_created)

    # 4. Helper
    print("[4] Creating helper...")
    helpers_path.mkdir(parents=True, exist_ok=True)
    helper_data = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 * @license    https://opensource.org/licenses/OSL-3.0 Open Software License v. 3.0 (OSL-3.0)
 */

/**
 * {module} Data Helper
 */
class {namespace}_{module}_Helper_Data extends Mage_Core_Helper_Abstract
{{
}}
"""
    (helpers_path / "Data.php").write_text(helper_data)
    files_created.append(str(helpers_path / "Data.php"))

    # 5. Generate files for each entity
    print(f"\n[5] Generating {len(entities)} entities...")

    adminhtml_layout_handles = ""
    frontend_layout_handles = ""

    for entity in entities:
        entity_name = entity['name']
        entity_lower = entity_name.lower()
        entity_title = entity.get('title', entity_name)
        entity_class = entity_name.capitalize()
        fields = entity.get('fields', [])

        print(f"  - {entity_name}")

        # Generate entity files
        files_created.extend(generate_entity_files(
            namespace, module, entity, entities, code_path, year
        ))

        # Add layout handles
        # Check if entity has WYSIWYG editor fields
        has_wysiwyg = any(f.get('name', '') in ['content', 'description', 'bio'] or f.get('type') == 'text' for f in fields)
        adminhtml_layout_handles += generate_adminhtml_layout_handles(
            namespace.lower(), module.lower(), entity_lower, has_wysiwyg
        )

    # Generate frontend (only once for main entity, not per entity)
    if not config.get('skip_frontend'):
        frontend_layout_handles = generate_frontend_layout_handles(namespace, module, entities, config)
        generate_frontend_controller(namespace, module, entities, code_path, files_created)
        generate_related_entity_controllers(namespace, module, entities, config, code_path, files_created)
        generate_frontend_blocks(namespace, module, entities, code_path, files_created)
        generate_sidebar_blocks(namespace, module, entities, config, code_path, frontend_design_path, files_created)
        generate_frontend_templates(namespace, module, entities, config, files_created)

    # Generate URL rewrite observer if any entity has url_key
    if entities_with_url_key:
        print(f"\n[5.5] Generating URL rewrite observer for SEO-friendly URLs...")
        # Use the first entity with url_key as the primary (usually there's only one)
        primary_entity = entities_with_url_key[0]
        generate_url_rewrite_observer(
            namespace, module,
            primary_entity['name'],
            primary_entity['name'].capitalize(),
            code_path,
            files_created
        )

    # 6. Layout XML
    print("\n[6] Creating layout XML...")

    # Adminhtml Layout
    adminhtml_layout_path.parent.mkdir(parents=True, exist_ok=True)
    adminhtml_layout_xml = f"""<?xml version="1.0"?>
<layout>
{adminhtml_layout_handles}</layout>
"""
    adminhtml_layout_path.write_text(adminhtml_layout_xml)
    files_created.append(str(adminhtml_layout_path))

    # Frontend Layout
    frontend_layout_path.parent.mkdir(parents=True, exist_ok=True)
    frontend_layout_xml = f"""<?xml version="1.0"?>
<layout>
{frontend_layout_handles}</layout>
"""
    frontend_layout_path.write_text(frontend_layout_xml)
    files_created.append(str(frontend_layout_path))

    # 7. Database setup script
    if entities:
        print("\n[7] Creating database setup script...")
        sql_path.mkdir(parents=True, exist_ok=True)
        setup_script = generate_setup_script(namespace, module, entities, year, relationships)
        setup_file = sql_path / "install-1.0.0.php"
        setup_file.write_text(setup_script)
        files_created.append(str(setup_file))

    # Frontend templates are now generated by frontend_generator.py (step 5)

    print(f"\n✅ Module generated successfully!")
    print(f"   Created {len(files_created)} files")
    print(f"\nNext steps:")
    print(f"  1. composer dump-autoload")
    print(f"  2. ./maho cache:flush")
    print(f"  3. Access admin menu: {config.get('menu_title', module)}")

    return files_created


def generate_entity_files(namespace, module, entity, all_entities, code_path, year):
    """Generate all files for a single entity using modular generators"""
    files_created = []

    # Extract entity properties
    entity_name = entity['name']
    entity_class = entity_name.capitalize()
    entity_title = entity.get('title', entity_name)
    fields = entity.get('fields', [])

    # Generate Model, Resource, Collection
    generate_model_files(namespace, module, entity_name, entity_class, fields, code_path, files_created, entity.get('multi_store', False))

    # Generate Admin CRUD (controller + blocks)
    generate_admin_controller(namespace, module, entity_name, entity_class, fields, code_path, files_created)
    generate_admin_blocks(namespace, module, entity, all_entities, code_path, files_created)

    # Frontend is now generated once for all entities (not per-entity)

    return files_created




def map_field_type_to_ddl(field_type):
    """Map JSON field type to Maho DDL type constant"""
    type_map = {
        'varchar': 'Maho\\Db\\Ddl\\Table::TYPE_TEXT',
        'text': 'Maho\\Db\\Ddl\\Table::TYPE_TEXT',
        'int': 'Maho\\Db\\Ddl\\Table::TYPE_INTEGER',
        'smallint': 'Maho\\Db\\Ddl\\Table::TYPE_SMALLINT',
        'datetime': 'Maho\\Db\\Ddl\\Table::TYPE_DATETIME',
        'timestamp': 'Maho\\Db\\Ddl\\Table::TYPE_TIMESTAMP',
        'decimal': 'Maho\\Db\\Ddl\\Table::TYPE_DECIMAL',
        'bool': 'Maho\\Db\\Ddl\\Table::TYPE_BOOLEAN',
    }
    return type_map.get(field_type.lower(), 'Maho\\Db\\Ddl\\Table::TYPE_TEXT')


def generate_column_definition(field):
    """Generate a single column definition from field config"""
    field_name = field['name']
    field_type = field.get('type', 'varchar')
    ddl_type = map_field_type_to_ddl(field_type)

    # Determine length
    if field_type in ['varchar', 'text']:
        raw_length = field.get('length', 255 if field_type == 'varchar' else '64k')
        # Quote string lengths like '64k', '2M', etc.
        if isinstance(raw_length, str):
            length = f"'{raw_length}'"
        else:
            length = str(raw_length)
    elif field_type == 'decimal':
        length = f"'{field.get('length', '12,4')}'"
    else:
        length = 'null'

    # Build options
    options = []

    # Nullable
    is_required = field.get('required', False)
    if field_type not in ['timestamp']:  # timestamps have special handling
        options.append(f"        'nullable'  => {'false' if is_required else 'true'},")

    # Default value (TEXT/BLOB columns cannot have defaults in MySQL)
    if 'default' in field and field_type not in ['text', 'textarea', 'wysiwyg']:
        default_val = field['default']
        if isinstance(default_val, str):
            options.append(f"        'default'   => '{default_val}',")
        elif isinstance(default_val, bool):
            options.append(f"        'default'   => {'true' if default_val else 'false'},")
        else:
            options.append(f"        'default'   => '{default_val}',")

    # Unsigned for integers
    if field_type in ['int', 'smallint'] and field.get('unsigned', False):
        options.append(f"        'unsigned'  => true,")

    # Unique index
    # Handled separately after table creation

    # Comment
    comment = field.get('comment', field_name.replace('_', ' ').title())
    options.append(f"        'comment'   => '{comment}',")

    options_str = "\n".join(options)

    return f"""    ->addColumn('{field_name}', {ddl_type}, {length}, [
{options_str}
    ], '{comment}')"""


def generate_setup_script(namespace, module, entities, year, relationships=None):
    """Generate database setup script with relationship tables"""
    tables = ""

    for entity_idx, entity in enumerate(entities):
        entity_lower = entity['name'].lower()
        table_name = f"{namespace.lower()}_{module.lower()}_{entity_lower}"
        id_field = f"{entity_lower}_id"
        fields = entity.get('fields', [])

        # Generate ID column
        columns = f"""    ->addColumn('{id_field}', Maho\\Db\\Ddl\\Table::TYPE_INTEGER, null, [
        'identity'  => true,
        'unsigned'  => true,
        'nullable'  => false,
        'primary'   => true,
        'comment'   => 'ID',
    ], 'ID')"""

        # Generate columns from field definitions
        # Skip the primary key field as it's already generated above
        for field in fields:
            if field['name'] == id_field:
                continue  # Skip primary key - already added
            columns += "\n" + generate_column_definition(field)

        # Add standard columns (only if not already defined)
        field_names = [f['name'] for f in fields]

        # Add url_key for main entity (first entity with frontend)
        if entity_idx == 0 and 'url_key' not in field_names:
            columns += """
    ->addColumn('url_key', Maho\\Db\\Ddl\\Table::TYPE_VARCHAR, 255, [
        'nullable'  => true,
        'comment'   => 'URL Key',
    ], 'URL Key')"""

        if 'status' not in field_names:
            columns += """
    ->addColumn('status', Maho\\Db\\Ddl\\Table::TYPE_SMALLINT, null, [
        'nullable'  => false,
        'default'   => '1',
        'comment'   => 'Status',
    ], 'Status')"""

        columns += """
    ->addColumn('created_at', Maho\\Db\\Ddl\\Table::TYPE_TIMESTAMP, null, [
        'nullable'  => false,
        'default'   => Maho\\Db\\Ddl\\Table::TIMESTAMP_INIT,
        'comment'   => 'Created At',
    ], 'Created At')
    ->addColumn('updated_at', Maho\\Db\\Ddl\\Table::TYPE_TIMESTAMP, null, [
        'nullable'  => false,
        'default'   => Maho\\Db\\Ddl\\Table::TIMESTAMP_INIT_UPDATE,
        'comment'   => 'Updated At',
    ], 'Updated At')"""

        tables += f"""
$table = $installer->getConnection()
    ->newTable($installer->getTable('{namespace.lower()}_{module.lower()}/{entity_lower}'))
{columns}
    ->setComment('{entity['name']} Table');

$installer->getConnection()->createTable($table);

"""

    # Add relationship tables
    if relationships:
        for rel in relationships:
            entity1, entity2 = rel
            rel_table_name = f"{entity1}_{entity2}"
            tables += f"""
/**
 * Create relationship table '{namespace.lower()}_{module.lower()}/{rel_table_name}'
 */
$table = $installer->getConnection()
    ->newTable($installer->getTable('{namespace.lower()}_{module.lower()}/{rel_table_name}'))
    ->addColumn('{entity1}_id', Maho\\Db\\Ddl\\Table::TYPE_INTEGER, null, [
        'unsigned'  => true,
        'nullable'  => false,
        'primary'   => true,
    ], '{entity1.capitalize()} ID')
    ->addColumn('{entity2}_id', Maho\\Db\\Ddl\\Table::TYPE_INTEGER, null, [
        'unsigned'  => true,
        'nullable'  => false,
        'primary'   => true,
    ], '{entity2.capitalize()} ID')
    ->addColumn('position', Maho\\Db\\Ddl\\Table::TYPE_INTEGER, null, [
        'nullable'  => false,
        'default'   => '0',
    ], 'Position')
    ->addIndex(
        $installer->getIdxName('{namespace.lower()}_{module.lower()}/{rel_table_name}', ['{entity2}_id']),
        ['{entity2}_id']
    )
    ->addForeignKey(
        $installer->getFkName('{namespace.lower()}_{module.lower()}/{rel_table_name}', '{entity1}_id', '{namespace.lower()}_{module.lower()}/{entity1}', '{entity1}_id'),
        '{entity1}_id',
        $installer->getTable('{namespace.lower()}_{module.lower()}/{entity1}'),
        '{entity1}_id',
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE,
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE
    )
    ->addForeignKey(
        $installer->getFkName('{namespace.lower()}_{module.lower()}/{rel_table_name}', '{entity2}_id', '{namespace.lower()}_{module.lower()}/{entity2}', '{entity2}_id'),
        '{entity2}_id',
        $installer->getTable('{namespace.lower()}_{module.lower()}/{entity2}'),
        '{entity2}_id',
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE,
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE
    )
    ->setComment('{entity1.capitalize()} to {entity2.capitalize()} Relationship Table');

$installer->getConnection()->createTable($table);

"""

    # Add store relationship tables for entities with multi_store enabled
    for entity in entities:
        if entity.get('multi_store', False):
            entity_lower = entity['name'].lower()
            id_field = f"{entity_lower}_id"
            store_table_name = f"{entity_lower}_store"

            tables += f"""
/**
 * Create store relationship table '{namespace.lower()}_{module.lower()}/{store_table_name}'
 */
$table = $installer->getConnection()
    ->newTable($installer->getTable('{namespace.lower()}_{module.lower()}/{store_table_name}'))
    ->addColumn('{id_field}', Maho\\Db\\Ddl\\Table::TYPE_INTEGER, null, [
        'unsigned'  => true,
        'nullable'  => false,
        'primary'   => true,
    ], '{entity['name']} ID')
    ->addColumn('store_id', Maho\\Db\\Ddl\\Table::TYPE_SMALLINT, null, [
        'unsigned'  => true,
        'nullable'  => false,
        'primary'   => true,
    ], 'Store ID')
    ->addIndex(
        $installer->getIdxName('{namespace.lower()}_{module.lower()}/{store_table_name}', ['store_id']),
        ['store_id']
    )
    ->addForeignKey(
        $installer->getFkName('{namespace.lower()}_{module.lower()}/{store_table_name}', '{id_field}', '{namespace.lower()}_{module.lower()}/{entity_lower}', '{id_field}'),
        '{id_field}',
        $installer->getTable('{namespace.lower()}_{module.lower()}/{entity_lower}'),
        '{id_field}',
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE,
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE
    )
    ->addForeignKey(
        $installer->getFkName('{namespace.lower()}_{module.lower()}/{store_table_name}', 'store_id', 'core/store', 'store_id'),
        'store_id',
        $installer->getTable('core/store'),
        'store_id',
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE,
        Maho\\Db\\Ddl\\Table::ACTION_CASCADE
    )
    ->setComment('{entity['name']} to Store Relationship Table');

$installer->getConnection()->createTable($table);

"""

    return f"""<?php
/**
 * Maho
 *
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 * @license    https://opensource.org/licenses/OSL-3.0 Open Software License v. 3.0 (OSL-3.0)
 */

$installer = $this;
$installer->startSetup();

{tables}
$installer->endSetup();
"""


def prompt_for_namespace(config):
    """Prompt user for namespace if not provided or needs confirmation"""

    current_namespace = config.get('namespace', '')
    module_name = config.get('module', 'Unknown')

    print("\n" + "="*60)
    print("MODULE NAMESPACE CONFIGURATION")
    print("="*60)

    if current_namespace:
        print(f"\nConfig specifies namespace: {current_namespace}")
        print(f"Full module name will be: {current_namespace}_{module_name}")

        # Show namespace options
        print("\nNamespace Options:")
        print("  1. Keep '{0}' (as specified in config)".format(current_namespace))
        print("  2. Use 'Maho' (Maho core namespace)")
        print("  3. Enter custom namespace")

        choice = input("\nSelect option [1-3] (default: 1): ").strip() or "1"

        if choice == "1":
            return current_namespace
        elif choice == "2":
            namespace = "Maho"
        elif choice == "3":
            namespace = input("Enter custom namespace (e.g., YourCompany): ").strip()
        else:
            print("Invalid choice, using config value: {0}".format(current_namespace))
            return current_namespace
    else:
        print("\n⚠️  No namespace specified in config!")
        print("\nNamespace Options:")
        print("  1. Use 'Maho' (Maho core namespace)")
        print("  2. Enter custom namespace")

        choice = input("\nSelect option [1-2]: ").strip()

        if choice == "1":
            namespace = "Maho"
        elif choice == "2":
            namespace = input("Enter custom namespace (e.g., YourCompany): ").strip()
        else:
            print("❌ Invalid choice")
            sys.exit(1)

    if not namespace:
        print("❌ Namespace cannot be empty")
        sys.exit(1)

    # Validate namespace format (PascalCase, no spaces/special chars)
    if not namespace.replace('_', '').isalnum() or not namespace[0].isupper():
        print(f"❌ Invalid namespace format: {namespace}")
        print("   Namespace must be PascalCase (e.g., Maho, YourCompany)")
        sys.exit(1)

    print(f"\n✓ Using namespace: {namespace}")
    print(f"✓ Full module name: {namespace}_{module_name}")

    confirm = input("\nProceed with this configuration? [Y/n]: ").strip().lower()
    if confirm and confirm != 'y':
        print("Aborted by user")
        sys.exit(0)

    return namespace


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate-module.py config.json [namespace]")
        print("\nExamples:")
        print("  python generate-module.py blog.json              # Interactive prompt")
        print("  python generate-module.py blog.json Maho         # Use Maho namespace")
        print("  python generate-module.py blog.json YourCompany  # Use custom namespace")
        sys.exit(1)

    config_file = sys.argv[1]
    namespace_arg = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)

    # Support both JSON and YAML config files
    with open(config_file) as f:
        if config_file.endswith(('.yaml', '.yml')):
            config = yaml.safe_load(f)
        else:
            config = json.load(f)

    # Use command-line namespace if provided, otherwise prompt
    if namespace_arg:
        # Validate namespace format
        if not namespace_arg.replace('_', '').isalnum() or not namespace_arg[0].isupper():
            print(f"❌ Invalid namespace format: {namespace_arg}")
            print("   Namespace must be PascalCase (e.g., Maho, YourCompany)")
            sys.exit(1)

        config['namespace'] = namespace_arg
        print(f"\n✓ Using namespace from argument: {namespace_arg}")
        print(f"✓ Full module name: {namespace_arg}_{config.get('module', 'Unknown')}")
    else:
        # Interactive namespace prompt (for direct Python execution)
        try:
            config['namespace'] = prompt_for_namespace(config)
        except EOFError:
            print("\n❌ Interactive input not available in this context")
            print("   Please provide namespace as argument:")
            print(f"   python generate-module.py {config_file} YourNamespace")
            sys.exit(1)

    try:
        generate_module(config)
        print("\n✅ SUCCESS - Module generated and ready to use!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
