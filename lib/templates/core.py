"""
Core templates for MahoCommerce module generation.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""


def module_declaration(namespace: str, module_name: str, code_pool: str, depends: list = None) -> str:
    """
    Generate module declaration XML for app/etc/modules/

    Args:
        namespace: Module namespace (e.g., 'Maho')
        module_name: Module name (e.g., 'Faq')
        code_pool: Code pool location ('core', 'community', 'local')
        depends: List of module dependencies

    Returns:
        XML string for module declaration
    """
    depends = depends or ['Mage_Core']

    depends_xml = '\n'.join([f'                <{dep}/>' for dep in depends])

    return f'''<?xml version="1.0"?>
<!--
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module_name}
 * @copyright  Copyright (c) 2025 Maho (https://mahocommerce.com)
 */
-->
<config>
    <modules>
        <{namespace}_{module_name}>
            <active>true</active>
            <codePool>{code_pool}</codePool>
            <depends>
{depends_xml}
            </depends>
        </{namespace}_{module_name}>
    </modules>
</config>
'''


def helper_class(namespace: str, module_name: str) -> str:
    """
    Generate default Helper/Data.php class

    Args:
        namespace: Module namespace
        module_name: Module name

    Returns:
        PHP code for helper class
    """
    return f'''<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module_name}
 * @copyright  Copyright (c) 2025 Maho (https://mahocommerce.com)
 */

/**
 * {module_name} helper
 *
 * @category   {namespace}
 * @package    {namespace}_{module_name}
 */
class {namespace}_{module_name}_Helper_Data extends Mage_Core_Helper_Abstract
{{
    /**
     * Get module configuration value
     *
     * @param string $path
     * @param mixed $store
     * @return mixed
     */
    public function getConfig(string $path, mixed $store = null): mixed
    {{
        return Mage::getStoreConfig('{namespace.lower()}_{module_name.lower()}/' . $path, $store);
    }}

    /**
     * Check if module is enabled
     *
     * @param mixed $store
     * @return bool
     */
    public function isEnabled(mixed $store = null): bool
    {{
        return (bool) $this->getConfig('general/enabled', $store);
    }}
}}
'''


def adminhtml_xml(namespace: str, module_name: str, entities: list) -> str:
    """
    Generate adminhtml.xml with ACL configuration

    Args:
        namespace: Module namespace
        module_name: Module name
        entities: List of entity configurations

    Returns:
        XML string for adminhtml.xml
    """
    module_key = f'{namespace.lower()}_{module_name.lower()}'

    # Build ACL resources for each entity
    acl_resources = []
    for entity in entities:
        entity_name = entity['name']
        entity_label = entity.get('label', entity_name.replace('_', ' ').title())

        acl_resources.append(f'''                        <{entity_name} translate="title">
                            <title>{entity_label}</title>
                        </{entity_name}>''')

    acl_xml = '\n'.join(acl_resources)

    return f'''<?xml version="1.0"?>
<!--
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module_name}
 * @copyright  Copyright (c) 2025 Maho (https://mahocommerce.com)
 */
-->
<config>
    <acl>
        <resources>
            <admin>
                <children>
                    <{module_key} translate="title">
                        <title>{module_name}</title>
                        <sort_order>100</sort_order>
                        <children>
{acl_xml}
                        </children>
                    </{module_key}>
                </children>
            </admin>
        </resources>
    </acl>
</config>
'''
