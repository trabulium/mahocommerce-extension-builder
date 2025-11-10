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

    # Use first entity as primary
    primary_entity = entities[0]
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
                'link' => $this->getUrl('*/*/')
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

    # Use first entity as primary
    primary_entity = entities[0]
    entity_name = primary_entity['name']
    entity_class = entity_name.capitalize()

    block_path = code_path / "Block"
    block_path.mkdir(parents=True, exist_ok=True)

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
            $this->_collection->addFieldToFilter('status', 1);

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

    # Use first entity as primary
    primary_entity = entities[0]
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
    primary_entity = entities[0]
    entity_name = primary_entity['name']

    frontend_route = config.get('frontend_route', module.lower())

    return f"""
    <!-- Index (List) Page -->
    <{frontend_route}_index_index>
        <reference name="root">
            <action method="setTemplate"><template>page/2columns-right.phtml</template></action>
        </reference>
        <reference name="content">
            <block type="{namespace.lower()}_{module.lower()}/list" name="{entity_name}.list" template="{namespace.lower()}/{module.lower()}/list.phtml" />
        </reference>
    </{frontend_route}_index_index>

    <!-- View (Detail) Page -->
    <{frontend_route}_index_view>
        <reference name="root">
            <action method="setTemplate"><template>page/2columns-right.phtml</template></action>
        </reference>
        <reference name="content">
            <block type="{namespace.lower()}_{module.lower()}/view" name="{entity_name}.view" template="{namespace.lower()}/{module.lower()}/view.phtml" />
        </reference>
    </{frontend_route}_index_view>
"""


def generate_sidebar_blocks(namespace, module, entities, config, code_path, files_created):
    """
    Generate sidebar blocks (categories, tags, etc.)

    Args:
        namespace: Module namespace
        module: Module name
        entities: List of all entities
        config: Module configuration
        code_path: Path to module root
        files_created: List to append created files to
    """
    # Generate sidebar blocks for category and tag entities if they exist
    # This creates blocks that can be added to the sidebar in layouts
    pass
