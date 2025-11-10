"""
Model file generation for MahoCommerce modules.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""

from pathlib import Path


def generate_model_files(namespace, module, entity_name, entity_class, fields, code_path, files_created, multi_store=False):
    """
    Generate Model, Resource Model, and Collection files for an entity

    Args:
        namespace: Module namespace (e.g., 'Maho')
        module: Module name (e.g., 'Blog')
        entity_name: Entity name lowercase (e.g., 'post')
        entity_class: Entity class name (e.g., 'Post')
        fields: List of field dicts
        code_path: Path object to module root (e.g., app/code/core/Maho/Blog)
        files_created: List to append created file paths to
        multi_store: Whether entity supports multi-store
    """
    model_path = code_path / "Model"
    model_path.mkdir(parents=True, exist_ok=True)

    # 1. Generate main Model class
    model_file = model_path / f"{entity_class}.php"
    model_file.write_text(_generate_model_class(namespace, module, entity_name, entity_class, multi_store))
    files_created.append(str(model_file))

    # 2. Generate Resource Model
    resource_path = model_path / "Resource"
    resource_path.mkdir(parents=True, exist_ok=True)
    resource_file = resource_path / f"{entity_class}.php"
    resource_file.write_text(_generate_resource_model(namespace, module, entity_name, entity_class, fields, multi_store))
    files_created.append(str(resource_file))

    # 3. Generate Collection
    collection_path = resource_path / entity_class
    collection_path.mkdir(parents=True, exist_ok=True)
    collection_file = collection_path / "Collection.php"
    collection_file.write_text(_generate_collection(namespace, module, entity_name, entity_class, multi_store))
    files_created.append(str(collection_file))


def _generate_model_class(namespace, module, entity_name, entity_class, multi_store):
    """Generate the main Model class"""
    from datetime import datetime
    year = datetime.now().year

    return f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {entity_class} Model
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Model_{entity_class} extends Mage_Core_Model_Abstract
{{
    const STATUS_ENABLED  = 1;
    const STATUS_DISABLED = 0;

    protected $_eventPrefix = '{namespace.lower()}_{module.lower()}_{entity_name}';
    protected $_eventObject = '{entity_name}';

    protected function _construct(): void
    {{
        $this->_init('{namespace.lower()}_{module.lower()}/{entity_name}');
    }}

    /**
     * Get available statuses
     *
     * @return array
     */
    public static function getAvailableStatuses(): array
    {{
        return [
            self::STATUS_ENABLED  => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Enabled'),
            self::STATUS_DISABLED => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Disabled'),
        ];
    }}
}}
"""


def _generate_resource_model(namespace, module, entity_name, entity_class, fields, multi_store):
    """Generate Resource Model class"""
    from datetime import datetime
    year = datetime.now().year

    # Determine ID field name
    id_field = f'{entity_name}_id'
    for field in fields:
        if field.get('primary') or field['name'] == id_field:
            id_field = field['name']
            break

    return f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {entity_class} Resource Model
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Model_Resource_{entity_class} extends Mage_Core_Model_Resource_Db_Abstract
{{
    protected function _construct(): void
    {{
        $this->_init('{namespace.lower()}_{module.lower()}/{entity_name}', '{id_field}');
    }}
}}
"""


def _generate_collection(namespace, module, entity_name, entity_class, multi_store):
    """Generate Collection class"""
    from datetime import datetime
    year = datetime.now().year

    return f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {entity_class} Collection
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Model_Resource_{entity_class}_Collection extends Mage_Core_Model_Resource_Db_Collection_Abstract
{{
    protected function _construct(): void
    {{
        $this->_init('{namespace.lower()}_{module.lower()}/{entity_name}');
    }}

    /**
     * Convert collection to option array for dropdowns
     *
     * @return array
     */
    public function toOptionArray(): array
    {{
        return $this->_toOptionArray('{entity_name}_id', 'name');
    }}

    /**
     * Convert collection to option hash for filters
     *
     * @return array
     */
    public function toOptionHash(): array
    {{
        return $this->_toOptionHash('{entity_name}_id', 'name');
    }}
}}
"""
