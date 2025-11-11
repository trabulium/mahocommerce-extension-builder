"""
Frontend interface generation for MahoCommerce modules.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""

from pathlib import Path
from datetime import datetime


def generate_frontend_controller(namespace, module, entities, code_path, files_created):
    """
    Generate frontend controller (index/view actions)

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        code_path: Path to module root
        files_created: List to append created files to
    """
    year = datetime.now().year

    # Use first entity with frontend enabled, fall back to first entity
    primary_entity = next((e for e in entities if e.get('frontend', {}).get('enabled', False)), entities[0])
    entity_name = primary_entity['name']
    entity_class = entity_name.capitalize()

    controller_path = code_path / "controllers"
    controller_path.mkdir(parents=True, exist_ok=True)

    controller_file = controller_path / "IndexController.php"

    controller_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * Frontend Index Controller
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_IndexController extends Mage_Core_Controller_Front_Action
{{
    /**
     * Index action - list all items
     */
    public function indexAction(): void
    {{
        $this->loadLayout();
        $this->_initLayoutMessages('customer/session');
        $this->_initLayoutMessages('catalog/session');

        $this->getLayout()->getBlock('head')->setTitle(
            $this->__('{entity_class}')
        );

        // Add breadcrumbs
        if ($breadcrumbs = $this->getLayout()->getBlock('breadcrumbs')) {{
            $breadcrumbs->addCrumb('home', [
                'label' => $this->__('Home'),
                'title' => $this->__('Go to Home Page'),
                'link' => Mage::getBaseUrl()
            ]);
            $breadcrumbs->addCrumb('{entity_name}', [
                'label' => $this->__('{entity_class}'),
                'title' => $this->__('{entity_class}')
            ]);
        }}

        $this->renderLayout();
    }}

    /**
     * View action - view single item
     */
    public function viewAction(): void
    {{
        $id = $this->getRequest()->getParam('id');
        ${entity_name} = Mage::getModel('{namespace.lower()}_{module.lower()}/{entity_name}')->load($id);

        if (!${entity_name}->getId()) {{
            $this->norouteAction();
            return;
        }}

        Mage::register('current_{entity_name}', ${entity_name});

        $this->loadLayout();
        $this->_initLayoutMessages('customer/session');
        $this->_initLayoutMessages('catalog/session');

        // Set page title
        $title = ${entity_name}->getName() ?? ${entity_name}->getTitle() ?? 'View {entity_class}';
        $this->getLayout()->getBlock('head')->setTitle($title);

        // Add breadcrumbs
        if ($breadcrumbs = $this->getLayout()->getBlock('breadcrumbs')) {{
            $breadcrumbs->addCrumb('home', [
                'label' => $this->__('Home'),
                'title' => $this->__('Go to Home Page'),
                'link' => Mage::getBaseUrl()
            ]);
            $breadcrumbs->addCrumb('{entity_name}', [
                'label' => $this->__('{entity_class}'),
                'title' => $this->__('{entity_class}'),
                'link' => Mage::getUrl('*/*')
            ]);
            $breadcrumbs->addCrumb('view', [
                'label' => $title,
                'title' => $title
            ]);
        }}

        $this->renderLayout();
    }}
}}
"""

    controller_file.write_text(controller_content)
    files_created.append(str(controller_file))


def generate_related_entity_controllers(namespace, module, entities, config, code_path, files_created):
    """
    Generate controllers for related entities (e.g., CuisineController, AuthorController)
    These show filtered lists of the primary entity

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        config: Module configuration
        code_path: Path to module root
        files_created: List to append created files to
    """
    year = datetime.now().year

    # Get primary entity
    primary_entity = next((e for e in entities if e.get('frontend', {}).get('enabled', False)), None)
    if not primary_entity:
        return

    primary_entity_name = primary_entity['name']
    primary_entity_class = primary_entity_name.capitalize()

    # Get sidebar blocks config to find related entities
    sidebar_blocks_config = primary_entity.get('frontend', {}).get('sidebar_blocks', [])

    controller_path = code_path / "controllers"
    controller_path.mkdir(parents=True, exist_ok=True)

    # Generate controller for each related entity
    for block_config in sidebar_blocks_config:
        if 'entity' not in block_config:
            continue

        related_entity_name = block_config['entity']
        related_entity = next((e for e in entities if e['name'] == related_entity_name), None)
        if not related_entity:
            continue

        related_entity_class = related_entity_name.capitalize()

        controller_file = controller_path / f"{related_entity_class}Controller.php"

        controller_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {related_entity_class} Controller
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_{related_entity_class}Controller extends Mage_Core_Controller_Front_Action
{{
    /**
     * View action - show all {primary_entity_name}s for this {related_entity_name}
     */
    public function viewAction(): void
    {{
        $id = $this->getRequest()->getParam('id');
        ${related_entity_name} = Mage::getModel('{namespace.lower()}_{module.lower()}/{related_entity_name}')->load($id);

        if (!${related_entity_name}->getId()) {{
            $this->norouteAction();
            return;
        }}

        Mage::register('current_{related_entity_name}', ${related_entity_name});

        $this->loadLayout();
        $this->_initLayoutMessages('customer/session');
        $this->_initLayoutMessages('catalog/session');

        // Set page title
        $title = ${related_entity_name}->getName() ?? 'View {related_entity_class}';
        $this->getLayout()->getBlock('head')->setTitle($title);

        // Add breadcrumbs
        if ($breadcrumbs = $this->getLayout()->getBlock('breadcrumbs')) {{
            $breadcrumbs->addCrumb('home', [
                'label' => $this->__('Home'),
                'title' => $this->__('Go to Home Page'),
                'link' => Mage::getBaseUrl()
            ]);
            $breadcrumbs->addCrumb('{primary_entity_name}', [
                'label' => $this->__('{primary_entity_class}'),
                'title' => $this->__('{primary_entity_class}'),
                'link' => Mage::getUrl('{module.lower()}')
            ]);
            $breadcrumbs->addCrumb('view', [
                'label' => $title,
                'title' => $title
            ]);
        }}

        $this->renderLayout();
    }}
}}
"""

        controller_file.write_text(controller_content)
        files_created.append(str(controller_file))


def generate_frontend_blocks(namespace, module, entities, code_path, files_created):
    """
    Generate frontend block files (List, View)

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        code_path: Path to module root
        files_created: List to append created files to
    """
    year = datetime.now().year

    # Use first entity with frontend enabled, fall back to first entity
    primary_entity = next((e for e in entities if e.get('frontend', {}).get('enabled', False)), entities[0])
    entity_name = primary_entity['name']
    entity_class = entity_name.capitalize()
    multi_store = primary_entity.get('multi_store', False)

    block_path = code_path / "Block"
    block_path.mkdir(parents=True, exist_ok=True)

    # Add store filter if multi_store is enabled
    store_filter_code = ""
    if multi_store:
        store_filter_code = """
            // Filter by current store
            $this->_collection->addStoreFilter(Mage::app()->getStore());
"""

    # 1. List block
    list_file = block_path / "List.php"
    list_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {entity_class} List Block
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Block_List extends Mage_Core_Block_Template
{{
    protected $_collection;

    /**
     * Get collection
     *
     * @return {namespace}_{module}_Model_Resource_{entity_class}_Collection
     */
    public function getCollection()
    {{
        if ($this->_collection === null) {{
            $this->_collection = Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{entity_name}_collection');

            // Filter by status if field exists
            $this->_collection->addFieldToFilter('status', 1);{store_filter_code}
            // Order by created_at descending
            $this->_collection->setOrder('created_at', 'DESC');

            // Setup pagination
            $this->_collection->setPageSize($this->getItemsPerPage());
            $this->_collection->setCurPage($this->getCurrentPage());
        }}

        return $this->_collection;
    }}

    /**
     * Get items per page
     *
     * @return int
     */
    public function getItemsPerPage(): int
    {{
        return (int) Mage::getStoreConfig('{namespace.lower()}_{module.lower()}/general/items_per_page') ?: 10;
    }}

    /**
     * Get current page number
     *
     * @return int
     */
    public function getCurrentPage(): int
    {{
        return (int) $this->getRequest()->getParam('p', 1);
    }}

    /**
     * Get item URL
     *
     * @param {namespace}_{module}_Model_{entity_class} $item
     * @return string
     */
    public function getItemUrl($item): string
    {{
        return $this->getUrl('*/*/view', ['id' => $item->getId()]);
    }}

    /**
     * Prepare layout
     *
     * @return $this
     */
    protected function _prepareLayout()
    {{
        parent::_prepareLayout();

        // Setup pager
        $pager = $this->getLayout()->createBlock('page/html_pager', '{entity_name}.pager');
        $pager->setCollection($this->getCollection());
        $this->setChild('pager', $pager);

        return $this;
    }}

    /**
     * Get pager HTML
     *
     * @return string
     */
    public function getPagerHtml(): string
    {{
        return $this->getChildHtml('pager');
    }}
}}
"""
    list_file.write_text(list_content)
    files_created.append(str(list_file))

    # 2. View block
    view_file = block_path / "View.php"
    view_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {entity_class} View Block
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Block_View extends Mage_Core_Block_Template
{{
    /**
     * Get current item
     *
     * @return {namespace}_{module}_Model_{entity_class}
     */
    public function get{entity_class}()
    {{
        return Mage::registry('current_{entity_name}');
    }}

    /**
     * Get back URL
     *
     * @return string
     */
    public function getBackUrl(): string
    {{
        return $this->getUrl('*/*/');
    }}
}}
"""
    view_file.write_text(view_content)
    files_created.append(str(view_file))


def generate_frontend_templates(namespace, module, entities, config, files_created):
    """
    Generate frontend template files

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        config: Module configuration
        files_created: List to append created files to
    """
    year = datetime.now().year

    # Use first entity with frontend enabled, fall back to first entity
    primary_entity = next((e for e in entities if e.get('frontend', {}).get('enabled', False)), entities[0])
    entity_name = primary_entity['name']
    entity_class = entity_name.capitalize()
    fields = primary_entity.get('fields', [])

    # Create template directory
    template_base = Path(f"../../../app/design/frontend/base/default/template/{namespace.lower()}/{module.lower()}")
    template_base.mkdir(parents=True, exist_ok=True)

    # 1. List template
    list_template = template_base / "list.phtml"
    list_content = f"""<?php
/**
 * Maho
 *
 * @category   design
 * @package    base_default
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 *
 * @var {namespace}_{module}_Block_List $this
 */
?>
<div class="{entity_name}-list">
    <div class="page-title">
        <h1><?php echo $this->__('{entity_class}') ?></h1>
    </div>

    <?php if ($this->getCollection()->getSize()): ?>
        <div class="{entity_name}-items">
            <?php foreach ($this->getCollection() as $item): ?>
                <div class="{entity_name}-item">
                    <h2>
                        <a href="<?php echo $this->getItemUrl($item) ?>">
                            <?php echo $this->escapeHtml($item->getName() ?? $item->getTitle()) ?>
                        </a>
                    </h2>
                    <div class="item-meta">
                        <?php if ($item->getCreatedAt()): ?>
                            <span class="date"><?php echo $this->formatDate($item->getCreatedAt(), 'medium') ?></span>
                        <?php endif; ?>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>

        <?php echo $this->getPagerHtml() ?>
    <?php else: ?>
        <p class="note-msg">
            <?php echo $this->__('No items found.') ?>
        </p>
    <?php endif; ?>
</div>
"""
    list_template.write_text(list_content)
    files_created.append(str(list_template))

    # 2. View template
    view_template = template_base / "view.phtml"

    # Find content fields for display
    content_fields = []
    for field in fields:
        if field['name'] not in [f"{entity_name}_id", 'status', 'created_at', 'updated_at'] and field.get('type') in ['text', 'mediumtext', 'longtext']:
            content_fields.append(field['name'])

    view_content = f"""<?php
/**
 * Maho
 *
 * @category   design
 * @package    base_default
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 *
 * @var {namespace}_{module}_Block_View $this
 */
${entity_name} = $this->get{entity_class}();
?>
<div class="{entity_name}-view">
    <div class="page-title">
        <h1><?php echo $this->escapeHtml(${entity_name}->getName() ?? ${entity_name}->getTitle()) ?></h1>
    </div>

    <div class="{entity_name}-content">
"""

    for content_field in content_fields:
        view_content += f"""        <?php if (${entity_name}->get{content_field.capitalize()}()): ?>
            <div class="field-{content_field}">
                <?php echo $this->helper('core')->escapeHtml(${entity_name}->get{content_field.capitalize()}(), ['b', 'i', 'u', 'p', 'br', 'strong', 'em']) ?>
            </div>
        <?php endif; ?>
"""

    view_content += f"""    </div>

    <div class="actions">
        <a href="<?php echo $this->getBackUrl() ?>" class="button">
            <span><?php echo $this->__('Back to List') ?></span>
        </a>
    </div>
</div>
"""
    view_template.write_text(view_content)
    files_created.append(str(view_template))


def generate_frontend_layout_handles(namespace, module, entities, config):
    """
    Generate frontend layout XML handles

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        config: Module configuration

    Returns:
        XML string for layout handles
    """
    primary_entity = next((e for e in entities if e.get('frontend', {}).get('enabled', False)), entities[0])
    entity_name = primary_entity['name']

    # Layout handles use the module class alias (namespace_module), NOT the frontend route
    module_alias = f"{namespace.lower()}_{module.lower()}"

    # Get sidebar configuration
    sidebar_blocks_config = primary_entity.get('frontend', {}).get('sidebar_blocks', [])

    # Determine sidebar positions
    has_left_sidebar = any(b.get('position') == 'left' for b in sidebar_blocks_config)
    has_right_sidebar = any(b.get('position') == 'right' for b in sidebar_blocks_config)

    # Set page template based on sidebar configuration
    if has_left_sidebar and has_right_sidebar:
        page_template = "page/3columns.phtml"
    elif has_left_sidebar:
        page_template = "page/2columns-left.phtml"
    elif has_right_sidebar:
        page_template = "page/2columns-right.phtml"
    else:
        page_template = "page/1column.phtml"

    # Generate sidebar block references
    sidebar_xml = _generate_sidebar_layout_xml(module_alias, sidebar_blocks_config, namespace, module, entities)

    # Build base layout handles
    layout_xml = f"""
    <!-- Index (List) Page -->
    <{module_alias}_index_index>
        <reference name="root">
            <action method="setTemplate"><template>{page_template}</template></action>
        </reference>
        <reference name="content">
            <block type="{module_alias}/list" name="{entity_name}.list" template="{namespace.lower()}/{module.lower()}/list.phtml" />
        </reference>{sidebar_xml}
    </{module_alias}_index_index>

    <!-- View (Detail) Page -->
    <{module_alias}_index_view>
        <reference name="root">
            <action method="setTemplate"><template>{page_template}</template></action>
        </reference>
        <reference name="content">
            <block type="{module_alias}/view" name="{entity_name}.view" template="{namespace.lower()}/{module.lower()}/view.phtml" />
        </reference>{sidebar_xml}
    </{module_alias}_index_view>
"""

    # Generate layout handles for related entity views (cuisine, author, etc.)
    for block_config in sidebar_blocks_config:
        if 'entity' not in block_config:
            continue

        related_entity_name = block_config['entity']
        related_entity_class = related_entity_name.capitalize()

        layout_xml += f"""
    <!-- {related_entity_class} View Page (filtered {entity_name} list) -->
    <{module_alias}_{related_entity_name}_view>
        <reference name="root">
            <action method="setTemplate"><template>{page_template}</template></action>
        </reference>
        <reference name="content">
            <block type="{module_alias}/list" name="{entity_name}.list" template="{namespace.lower()}/{module.lower()}/list.phtml" />
        </reference>{sidebar_xml}
    </{module_alias}_{related_entity_name}_view>
"""

    return layout_xml


def _generate_sidebar_layout_xml(module_alias, sidebar_blocks_config, namespace, module, entities):
    """Generate sidebar layout XML blocks"""
    if not sidebar_blocks_config:
        return ""

    # Group blocks by position
    left_blocks = []
    right_blocks = []

    for block_config in sidebar_blocks_config:
        position = block_config.get('position', 'right')
        block_type = block_config.get('type')

        if block_type == 'recent':
            block_xml = f"""
            <block type="{module_alias}/sidebar_recent" name="{module.lower()}.sidebar.recent" template="{namespace.lower()}/{module.lower()}/sidebar/recent.phtml" />"""
        elif 'entity' in block_config:
            entity_name = block_config['entity']
            entity_class = entity_name.capitalize()
            entity_plural = entity_class + 's'
            block_xml = f"""
            <block type="{module_alias}/sidebar_{entity_plural.lower()}" name="{module.lower()}.sidebar.{entity_name}s" template="{namespace.lower()}/{module.lower()}/sidebar/{entity_name}s.phtml" />"""
        else:
            continue

        if position == 'left':
            left_blocks.append(block_xml)
        else:  # default to right
            right_blocks.append(block_xml)

    # Build sidebar XML
    sidebar_xml = ""
    if left_blocks:
        sidebar_xml += "\n        <reference name=\"left\">"
        sidebar_xml += "".join(left_blocks)
        sidebar_xml += "\n        </reference>"
    if right_blocks:
        sidebar_xml += "\n        <reference name=\"right\">"
        sidebar_xml += "".join(right_blocks)
        sidebar_xml += "\n        </reference>"

    return sidebar_xml


def generate_sidebar_blocks(namespace, module, entities, config, code_path, design_path, files_created):
    """
    Generate sidebar blocks (related entities, recent items)

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        config: Module configuration
        code_path: Path to module root
        design_path: Path to design directory
        files_created: List to append created files to
    """
    from datetime import datetime
    year = datetime.now().year

    # Find primary entity with frontend enabled
    primary_entity = next((e for e in entities if e.get('frontend', {}).get('enabled', False)), None)
    if not primary_entity:
        return

    sidebar_blocks_config = primary_entity.get('frontend', {}).get('sidebar_blocks', [])
    if not sidebar_blocks_config:
        return

    # Create sidebar block directory
    sidebar_path = code_path / "Block" / "Sidebar"
    sidebar_path.mkdir(parents=True, exist_ok=True)

    # Create sidebar template directory
    template_path = design_path / "template" / namespace.lower() / module.lower() / "sidebar"
    template_path.mkdir(parents=True, exist_ok=True)

    primary_entity_name = primary_entity['name']
    primary_entity_class = primary_entity_name.capitalize()

    # Generate blocks based on config
    for block_config in sidebar_blocks_config:
        block_type = block_config.get('type')

        if block_type == 'recent':
            # Generate Recent Items block
            _generate_recent_sidebar_block(
                namespace, module, primary_entity_name, primary_entity_class,
                year, sidebar_path, template_path, files_created
            )

        elif 'entity' in block_config:
            # Generate Related Entity browse block
            related_entity_name = block_config['entity']
            related_entity = next((e for e in entities if e['name'] == related_entity_name), None)
            if related_entity:
                _generate_entity_sidebar_block(
                    namespace, module, primary_entity_name, primary_entity_class,
                    related_entity, year, sidebar_path, template_path, files_created
                )


def _generate_recent_sidebar_block(namespace, module, entity_name, entity_class, year, sidebar_path, template_path, files_created):
    """Generate Recent Items sidebar block"""

    # PHP Block class
    block_file = sidebar_path / "Recent.php"
    block_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * Recent {entity_class} Sidebar Block
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Block_Sidebar_Recent extends Mage_Core_Block_Template
{{
    protected $_collection;

    /**
     * Get recent {entity_name} collection
     *
     * @return {namespace}_{module}_Model_Resource_{entity_class}_Collection
     */
    public function getRecent{entity_class}s()
    {{
        if ($this->_collection === null) {{
            $this->_collection = Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{entity_name}_collection');

            // Filter by status
            $this->_collection->addFieldToFilter('status', 1);

            // Filter by current store
            $this->_collection->addStoreFilter(Mage::app()->getStore());

            // Order by created_at descending
            $this->_collection->setOrder('created_at', 'DESC');

            // Limit to 5 most recent
            $this->_collection->setPageSize(5);
        }}

        return $this->_collection;
    }}

    /**
     * Get {entity_name} URL
     *
     * @param {namespace}_{module}_Model_{entity_class} ${entity_name}
     * @return string
     */
    public function get{entity_class}Url(${entity_name}): string
    {{
        return $this->getUrl('*/*/view', ['id' => ${entity_name}->getId()]);
    }}
}}
"""
    block_file.write_text(block_content)
    files_created.append(str(block_file))

    # Template
    template_file = template_path / "recent.phtml"
    template_content = f"""<?php
/**
 * Maho
 *
 * @category   design
 * @package    base_default
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 *
 * @var {namespace}_{module}_Block_Sidebar_Recent $this
 */
?>
<?php ${entity_name}s = $this->getRecent{entity_class}s(); ?>
<?php if (${entity_name}s && ${entity_name}s->getSize()): ?>
<div class="block block-{entity_name}-recent">
    <div class="block-title">
        <strong><span><?php echo $this->__('Recent {entity_class}s') ?></span></strong>
    </div>
    <div class="block-content">
        <ol class="mini-{entity_name}s-list">
            <?php foreach (${entity_name}s as ${entity_name}): ?>
                <li class="item">
                    <a href="<?php echo $this->get{entity_class}Url(${entity_name}) ?>" class="{entity_name}-name">
                        <?php echo $this->escapeHtml(${entity_name}->getName()) ?>
                    </a>
                    <?php if (${entity_name}->getPublishDate()): ?>
                        <div class="{entity_name}-date">
                            <?php echo $this->formatDate(${entity_name}->getPublishDate(), 'medium') ?>
                        </div>
                    <?php endif; ?>
                </li>
            <?php endforeach; ?>
        </ol>
    </div>
</div>
<?php endif; ?>
"""
    template_file.write_text(template_content)
    files_created.append(str(template_file))


def _generate_entity_sidebar_block(namespace, module, primary_entity_name, primary_entity_class,
                                   related_entity, year, sidebar_path, template_path, files_created):
    """Generate Related Entity sidebar block (e.g., Browse by Cuisine)"""

    related_entity_name = related_entity['name']
    related_entity_class = related_entity_name.capitalize()
    related_entity_plural = related_entity_class + 's'

    # PHP Block class
    block_file = sidebar_path / f"{related_entity_plural}.php"
    block_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {related_entity_plural} Sidebar Block
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Block_Sidebar_{related_entity_plural} extends Mage_Core_Block_Template
{{
    protected $_collection;

    /**
     * Get {related_entity_name} collection with {primary_entity_name} count
     *
     * @return {namespace}_{module}_Model_Resource_{related_entity_class}_Collection
     */
    public function get{related_entity_plural}()
    {{
        if ($this->_collection === null) {{
            $this->_collection = Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity_name}_collection');

            // Join with {primary_entity_name} table to count items
            $this->_collection->getSelect()
                ->joinLeft(
                    ['{primary_entity_name}' => $this->_collection->getTable('{namespace.lower()}_{module.lower()}/{primary_entity_name}')],
                    'main_table.{related_entity_name}_id = {primary_entity_name}.{related_entity_name}_id AND {primary_entity_name}.status = 1',
                    ['{primary_entity_name}_count' => new \\Maho\\Db\\Expr('COUNT({primary_entity_name}.{primary_entity_name}_id)')]
                )
                ->group('main_table.{related_entity_name}_id')
                ->having('COUNT({primary_entity_name}.{primary_entity_name}_id) > 0')
                ->order('name ASC');
        }}

        return $this->_collection;
    }}

    /**
     * Get {related_entity_name} URL
     *
     * @param {namespace}_{module}_Model_{related_entity_class} ${related_entity_name}
     * @return string
     */
    public function get{related_entity_class}Url(${related_entity_name}): string
    {{
        return Mage::getUrl('{module.lower()}/{related_entity_name}/view', ['id' => ${related_entity_name}->getId()]);
    }}
}}
"""
    block_file.write_text(block_content)
    files_created.append(str(block_file))

    # Template
    template_file = template_path / f"{related_entity_name}s.phtml"
    template_content = f"""<?php
/**
 * Maho
 *
 * @category   design
 * @package    base_default
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 *
 * @var {namespace}_{module}_Block_Sidebar_{related_entity_plural} $this
 */
?>
<?php ${related_entity_name}s = $this->get{related_entity_plural}(); ?>
<?php if (${related_entity_name}s && ${related_entity_name}s->getSize()): ?>
<div class="block block-{module.lower()}-{related_entity_name}s">
    <div class="block-title">
        <strong><span><?php echo $this->__('Browse by {related_entity_class}') ?></span></strong>
    </div>
    <div class="block-content">
        <ul class="{related_entity_name}-list">
            <?php foreach (${related_entity_name}s as ${related_entity_name}): ?>
                <li class="item">
                    <a href="<?php echo $this->get{related_entity_class}Url(${related_entity_name}) ?>">
                        <?php echo $this->escapeHtml(${related_entity_name}->getName()) ?>
                        <span class="count">(<?php echo (int)${related_entity_name}->getData('{primary_entity_name}_count') ?>)</span>
                    </a>
                </li>
            <?php endforeach; ?>
        </ul>
    </div>
</div>
<?php endif; ?>
"""
    template_file.write_text(template_content)
    files_created.append(str(template_file))
