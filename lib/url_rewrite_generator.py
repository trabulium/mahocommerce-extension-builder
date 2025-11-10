"""
URL rewrite generation for MahoCommerce modules.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""

from lib.utils import to_camel_case


def has_url_key_field(fields: list) -> bool:
    """
    Check if entity has a url_key field

    Args:
        fields: List of field configurations

    Returns:
        True if entity has url_key field
    """
    for field in fields:
        if field.get('name') == 'url_key':
            return True
    return False


def generate_url_rewrite_observer(namespace: str, module_name: str, entity: dict) -> str:
    """
    Generate URL rewrite observer for an entity

    Args:
        namespace: Module namespace
        module_name: Module name
        entity: Entity configuration

    Returns:
        PHP code for observer
    """
    entity_name = entity['name']
    entity_class = to_camel_case(entity_name)
    entity_label = entity.get('label', entity_name.replace('_', ' ').title())

    return f'''<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module_name}
 * @copyright  Copyright (c) 2025 Maho (https://mahocommerce.com)
 */

/**
 * URL rewrite observer for {entity_label}
 *
 * @category   {namespace}
 * @package    {namespace}_{module_name}
 */
class {namespace}_{module_name}_Model_Observer_UrlRewrite
{{
    /**
     * Generate URL rewrites after save
     *
     * @param Varien_Event_Observer $observer
     * @return void
     */
    public function generate{entity_class}UrlRewrite(Varien_Event_Observer $observer): void
    {{
        /** @var {namespace}_{module_name}_Model_{entity_class} ${entity_name} */
        ${entity_name} = $observer->getEvent()->get{entity_class}();

        if (!${entity_name}->getId()) {{
            return;
        }}

        // Generate URL key if not set
        if (!${entity_name}->getUrlKey()) {{
            $urlKey = $this->_generateUrlKey(${entity_name});
            ${entity_name}->setUrlKey($urlKey);
            ${entity_name}->getResource()->saveAttribute(${entity_name}, 'url_key');
        }}

        // Generate URL rewrite
        $this->_createUrlRewrite(${entity_name});
    }}

    /**
     * Generate URL key from name/title
     *
     * @param {namespace}_{module_name}_Model_{entity_class} ${entity_name}
     * @return string
     */
    protected function _generateUrlKey({namespace}_{module_name}_Model_{entity_class} ${entity_name}): string
    {{
        $name = ${entity_name}->getName() ?? ${entity_name}->getTitle() ?? '';
        $urlKey = Mage::helper('catalog/product_url')->format($name);

        // Ensure uniqueness
        $suffix = '';
        $i = 0;
        $collection = Mage::getResourceModel('{namespace.lower()}_{module_name.lower()}/{entity_name}_collection');

        do {{
            $collection->clear();
            $collection->addFieldToFilter('url_key', $urlKey . $suffix);
            if (${entity_name}->getId()) {{
                $collection->addFieldToFilter('{entity_name}_id', ['neq' => ${entity_name}->getId()]);
            }}

            if ($collection->getSize() > 0) {{
                $i++;
                $suffix = '-' . $i;
            }} else {{
                break;
            }}
        }} while (true);

        return $urlKey . $suffix;
    }}

    /**
     * Create URL rewrite
     *
     * @param {namespace}_{module_name}_Model_{entity_class} ${entity_name}
     * @return void
     */
    protected function _createUrlRewrite({namespace}_{module_name}_Model_{entity_class} ${entity_name}): void
    {{
        $stores = ${entity_name}->getStoreId() ? [${entity_name}->getStoreId()] : Mage::app()->getStores();

        foreach ($stores as $store) {{
            if ($store instanceof Mage_Core_Model_Store) {{
                $storeId = $store->getId();
            }} else {{
                $storeId = $store;
            }}

            // Delete old rewrite
            Mage::getModel('core/url_rewrite')
                ->getCollection()
                ->addFieldToFilter('id_path', '{namespace.lower()}_{module_name.lower()}/{entity_name}/' . ${entity_name}->getId())
                ->addFieldToFilter('store_id', $storeId)
                ->walk('delete');

            // Create new rewrite
            $urlRewrite = Mage::getModel('core/url_rewrite');
            $urlRewrite->setData([
                'store_id' => $storeId,
                'id_path' => '{namespace.lower()}_{module_name.lower()}/{entity_name}/' . ${entity_name}->getId(),
                'request_path' => '{namespace.lower()}_{module_name.lower()}/{entity_name}/' . ${entity_name}->getUrlKey(),
                'target_path' => '{namespace.lower()}_{module_name.lower()}/{entity_name}/view/id/' . ${entity_name}->getId(),
                'is_system' => 1,
            ]);

            try {{
                $urlRewrite->save();
            }} catch (Exception $e) {{
                Mage::logException($e);
            }}
        }}
    }}

    /**
     * Delete URL rewrites after delete
     *
     * @param Varien_Event_Observer $observer
     * @return void
     */
    public function delete{entity_class}UrlRewrite(Varien_Event_Observer $observer): void
    {{
        /** @var {namespace}_{module_name}_Model_{entity_class} ${entity_name} */
        ${entity_name} = $observer->getEvent()->get{entity_class}();

        if (!${entity_name}->getId()) {{
            return;
        }}

        // Delete all rewrites for this item
        Mage::getModel('core/url_rewrite')
            ->getCollection()
            ->addFieldToFilter('id_path', '{namespace.lower()}_{module_name.lower()}/{entity_name}/' . ${entity_name}->getId())
            ->walk('delete');
    }}
}}
'''


def add_url_rewrite_events(namespace: str, module_name: str, entity_name: str, entity_class: str) -> str:
    """
    Generate event configuration for URL rewrites

    Args:
        namespace: Module namespace
        module_name: Module name
        entity_name: Entity name (lowercase/snake_case)
        entity_class: Entity class name (CamelCase)

    Returns:
        XML configuration for events
    """
    event_prefix = f'{namespace.lower()}_{module_name.lower()}_{entity_name}'

    return f'''
        <!-- URL Rewrite Events -->
        <events>
            <{event_prefix}_save_after>
                <observers>
                    <{namespace.lower()}_{module_name.lower()}_url_rewrite>
                        <class>{namespace.lower()}_{module_name.lower()}/observer_urlRewrite</class>
                        <method>generate{entity_class}UrlRewrite</method>
                    </{namespace.lower()}_{module_name.lower()}_url_rewrite>
                </observers>
            </{event_prefix}_save_after>
            <{event_prefix}_delete_after>
                <observers>
                    <{namespace.lower()}_{module_name.lower()}_url_rewrite_delete>
                        <class>{namespace.lower()}_{module_name.lower()}/observer_urlRewrite</class>
                        <method>delete{entity_class}UrlRewrite</method>
                    </{namespace.lower()}_{module_name.lower()}_url_rewrite_delete>
                </observers>
            </{event_prefix}_delete_after>
        </events>'''
