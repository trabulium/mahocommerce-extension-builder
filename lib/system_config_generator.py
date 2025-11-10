"""
System configuration generation for MahoCommerce modules.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""


def present_system_config_suggestions(namespace: str, module_name: str, entities: list) -> str:
    """
    Present suggestions for system configuration

    Args:
        namespace: Module namespace
        module_name: Module name
        entities: List of entity configurations

    Returns:
        Formatted suggestions text or None to skip system config
    """
    # Return None to indicate no system config suggestions for now
    # This can be expanded later
    return None


def generate_system_xml(namespace: str, module_name: str, config: dict) -> str:
    """
    Generate system.xml configuration

    Args:
        namespace: Module namespace
        module_name: Module name
        config: Module configuration

    Returns:
        XML string for system.xml
    """
    module_key = f'{namespace.lower()}_{module_name.lower()}'
    module_label = config.get('label', module_name)

    # Build configuration fields
    fields = []

    # General settings
    fields.append('''            <general translate="label">
                <label>General Settings</label>
                <frontend_type>text</frontend_type>
                <sort_order>10</sort_order>
                <show_in_default>1</show_in_default>
                <show_in_website>1</show_in_website>
                <show_in_store>1</show_in_store>
                <fields>
                    <enabled translate="label">
                        <label>Enable Module</label>
                        <frontend_type>select</frontend_type>
                        <source_model>adminhtml/system_config_source_yesno</source_model>
                        <sort_order>10</sort_order>
                        <show_in_default>1</show_in_default>
                        <show_in_website>1</show_in_website>
                        <show_in_store>1</show_in_store>
                    </enabled>
                    <title translate="label comment">
                        <label>Module Title</label>
                        <frontend_type>text</frontend_type>
                        <sort_order>20</sort_order>
                        <show_in_default>1</show_in_default>
                        <show_in_website>1</show_in_website>
                        <show_in_store>1</show_in_store>
                        <comment>Display title for frontend pages</comment>
                    </title>
                    <items_per_page translate="label comment">
                        <label>Items Per Page</label>
                        <frontend_type>text</frontend_type>
                        <validate>validate-digits validate-greater-than-zero</validate>
                        <sort_order>30</sort_order>
                        <show_in_default>1</show_in_default>
                        <show_in_website>1</show_in_website>
                        <show_in_store>1</show_in_store>
                        <comment>Number of items to display per page on frontend</comment>
                    </items_per_page>
                </fields>
            </general>''')

    # SEO settings
    fields.append('''            <seo translate="label">
                <label>SEO Settings</label>
                <frontend_type>text</frontend_type>
                <sort_order>20</sort_order>
                <show_in_default>1</show_in_default>
                <show_in_website>1</show_in_website>
                <show_in_store>1</show_in_store>
                <fields>
                    <meta_title translate="label comment">
                        <label>Meta Title Template</label>
                        <frontend_type>text</frontend_type>
                        <sort_order>10</sort_order>
                        <show_in_default>1</show_in_default>
                        <show_in_website>1</show_in_website>
                        <show_in_store>1</show_in_store>
                        <comment>Use {{name}} for item name</comment>
                    </meta_title>
                    <meta_description translate="label comment">
                        <label>Meta Description Template</label>
                        <frontend_type>textarea</frontend_type>
                        <sort_order>20</sort_order>
                        <show_in_default>1</show_in_default>
                        <show_in_website>1</show_in_website>
                        <show_in_store>1</show_in_store>
                        <comment>Use {{name}} for item name, {{description}} for description</comment>
                    </meta_description>
                    <meta_keywords translate="label">
                        <label>Default Meta Keywords</label>
                        <frontend_type>textarea</frontend_type>
                        <sort_order>30</sort_order>
                        <show_in_default>1</show_in_default>
                        <show_in_website>1</show_in_website>
                        <show_in_store>1</show_in_store>
                    </meta_keywords>
                </fields>
            </seo>''')

    fields_xml = '\n'.join(fields)

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
    <tabs>
        <{module_key} translate="label">
            <label>{module_label}</label>
            <sort_order>200</sort_order>
        </{module_key}>
    </tabs>
    <sections>
        <{module_key} translate="label">
            <label>{module_label}</label>
            <tab>{module_key}</tab>
            <frontend_type>text</frontend_type>
            <sort_order>100</sort_order>
            <show_in_default>1</show_in_default>
            <show_in_website>1</show_in_website>
            <show_in_store>1</show_in_store>
            <groups>
{fields_xml}
            </groups>
        </{module_key}>
    </sections>
</config>
'''
