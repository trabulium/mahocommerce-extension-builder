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

    # Generate field mapping if multi_store is enabled
    field_mapping = ""
    if multi_store:
        field_mapping = f"""
        $this->_map['fields']['{entity_name}_id'] = 'main_table.{entity_name}_id';
        $this->_map['fields']['store']     = 'store_table.store_id';"""

    # Generate store filter methods if multi_store is enabled
    store_filter_methods = ""
    if multi_store:
        store_filter_methods = f"""
    /**
     * Add filter by store
     *
     * @param int|Mage_Core_Model_Store $store
     * @param bool $withAdmin
     * @return $this
     */
    public function addStoreFilter($store, $withAdmin = true)
    {{
        if (!$this->getFlag('store_filter_added')) {{
            if ($store instanceof Mage_Core_Model_Store) {{
                $store = [$store->getId()];
            }}

            if (!is_array($store)) {{
                $store = [$store];
            }}

            if ($withAdmin) {{
                $store[] = Mage_Core_Model_App::ADMIN_STORE_ID;
            }}

            $this->addFilter('store', ['in' => $store], 'public');
        }}
        return $this;
    }}

    /**
     * Join store relation table if there is store filter
     */
    #[\\Override]
    protected function _renderFiltersBefore()
    {{
        if ($this->getFilter('store')) {{
            $this->getSelect()->join(
                ['store_table' => $this->getTable('{namespace.lower()}_{module.lower()}/{entity_name}_store')],
                'main_table.{entity_name}_id = store_table.{entity_name}_id',
                [],
            )->group('main_table.{entity_name}_id');

            /*
             * Allow analytic functions usage because of one field grouping
             */
            $this->_useAnalyticFunction = true;
        }}
        return parent::_renderFiltersBefore();
    }}

    /**
     * Get SQL for get record count.
     * Extra GROUP BY strip added.
     *
     * @return Maho\\Db\\Select
     */
    #[\\Override]
    public function getSelectCountSql()
    {{
        $countSelect = parent::getSelectCountSql();

        $countSelect->reset(Maho\\Db\\Select::GROUP);

        return $countSelect;
    }}"""

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
        $this->_init('{namespace.lower()}_{module.lower()}/{entity_name}');{field_mapping}
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
    }}{store_filter_methods}
}}
"""
