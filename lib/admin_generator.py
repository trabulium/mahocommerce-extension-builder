"""
Admin interface generation for MahoCommerce modules.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""

from pathlib import Path
from datetime import datetime


def generate_admin_controller(namespace, module, entity_name, entity_class, fields, code_path, files_created):
    """
    Generate admin controller for an entity

    Args:
        namespace: Module namespace
        module: Module name
        entity_name: Entity name (lowercase)
        entity_class: Entity class name (CamelCase)
        fields: List of field dicts
        code_path: Path to module root
        files_created: List to append created files to
    """
    year = datetime.now().year
    controller_path = code_path / "controllers" / "Adminhtml"
    controller_path.mkdir(parents=True, exist_ok=True)

    controller_file = controller_path / f"{entity_class}Controller.php"

    # Find title field (name, title, or first varchar)
    title_field = entity_name + '_id'
    for field in fields:
        if field['name'] in ['name', 'title']:
            title_field = field['name']
            break
    if title_field == entity_name + '_id':
        for field in fields:
            if field.get('type') == 'varchar':
                title_field = field['name']
                break

    # Detect image fields for upload handling
    image_fields = []
    for field in fields:
        field_name = field['name']
        if field_name in ['image', 'avatar', 'photo', 'thumbnail'] or '_image' in field_name:
            image_fields.append(field_name)

    # Generate image upload code if needed
    image_upload_code = ""
    if image_fields:
        for img_field in image_fields:
            image_upload_code += f"""
            // Handle {img_field} upload
            if (isset($_FILES['{img_field}']['name']) && $_FILES['{img_field}']['name'] != '') {{
                try {{
                    $uploader = new Mage_Core_Model_File_Uploader('{img_field}');
                    $uploader->setAllowedExtensions(['jpg', 'jpeg', 'gif', 'png']);
                    $uploader->setAllowRenameFiles(true);
                    $uploader->setFilesDispersion(false);

                    $path = Mage::getBaseDir('media') . DS . '{namespace.lower()}_{module.lower()}' . DS . '{entity_name}' . DS;
                    if (!is_dir($path)) {{
                        mkdir($path, 0777, true);
                    }}

                    $uploader->save($path, $_FILES['{img_field}']['name']);
                    $data['{img_field}'] = '{namespace.lower()}_{module.lower()}/{entity_name}/' . $uploader->getUploadedFileName();
                }} catch (Exception $e) {{
                    if ($e->getCode() != Mage_Core_Model_File_Uploader::TMP_NAME_EMPTY) {{
                        Mage::getSingleton('adminhtml/session')->addError($e->getMessage());
                        $this->_redirect('*/*/edit', ['id' => $this->getRequest()->getParam('id')]);
                        return;
                    }}
                }}
            }} else {{
                // Handle delete checkbox
                if (isset($data['{img_field}']['delete']) && $data['{img_field}']['delete'] == 1) {{
                    $data['{img_field}'] = '';
                }} else {{
                    unset($data['{img_field}']);
                }}
            }}
"""

    controller_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

/**
 * {entity_class} Admin Controller
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Adminhtml_{entity_class}Controller extends Mage_Adminhtml_Controller_Action
{{
    public const ADMIN_RESOURCE = '{namespace.lower()}_{module.lower()}/{entity_name}';

    protected function _initAction(): static
    {{
        $this->loadLayout()
            ->_setActiveMenu('{namespace.lower()}_{module.lower()}/{entity_name}')
            ->_addBreadcrumb(
                Mage::helper('{namespace.lower()}_{module.lower()}')->__('{entity_class}'),
                Mage::helper('{namespace.lower()}_{module.lower()}')->__('{entity_class}')
            );
        return $this;
    }}

    public function indexAction(): void
    {{
        $this->_title($this->__('Manage {entity_class}'));
        $this->_initAction();
        $this->renderLayout();
    }}

    public function gridAction(): void
    {{
        $this->loadLayout();
        $this->renderLayout();
    }}

    public function newAction(): void
    {{
        $this->_forward('edit');
    }}

    public function editAction(): void
    {{
        $id = $this->getRequest()->getParam('id');
        $model = Mage::getModel('{namespace.lower()}_{module.lower()}/{entity_name}');

        if ($id) {{
            $model->load($id);
            if (!$model->getId()) {{
                Mage::getSingleton('adminhtml/session')->addError(
                    Mage::helper('{namespace.lower()}_{module.lower()}')->__('{entity_class} does not exist')
                );
                $this->_redirect('*/*/');
                return;
            }}
        }}

        $this->_title($model->getId() ? $model->getData('{title_field}') : $this->__('New {entity_class}'));

        $data = Mage::getSingleton('adminhtml/session')->getFormData(true);
        if (!empty($data)) {{
            $model->setData($data);
        }}

        Mage::register('current_{entity_name}', $model);

        $this->_initAction();
        $this->renderLayout();
    }}

    public function saveAction(): void
    {{
        if ($data = $this->getRequest()->getPost()) {{
            $id = $this->getRequest()->getParam('id');
            $model = Mage::getModel('{namespace.lower()}_{module.lower()}/{entity_name}');

            if ($id) {{
                $model->load($id);
            }}
{image_upload_code}
            $model->setData($data);

            try {{
                $model->save();

                Mage::getSingleton('adminhtml/session')->addSuccess(
                    Mage::helper('{namespace.lower()}_{module.lower()}')->__('{entity_class} was successfully saved')
                );
                Mage::getSingleton('adminhtml/session')->setFormData(false);

                if ($this->getRequest()->getParam('back')) {{
                    $this->_redirect('*/*/edit', ['id' => $model->getId()]);
                    return;
                }}
                $this->_redirect('*/*/');
                return;
            }} catch (Exception $e) {{
                Mage::getSingleton('adminhtml/session')->addError($e->getMessage());
                Mage::getSingleton('adminhtml/session')->setFormData($data);
                $this->_redirect('*/*/edit', ['id' => $this->getRequest()->getParam('id')]);
                return;
            }}
        }}
        $this->_redirect('*/*/');
    }}

    public function deleteAction(): void
    {{
        if ($id = $this->getRequest()->getParam('id')) {{
            try {{
                $model = Mage::getModel('{namespace.lower()}_{module.lower()}/{entity_name}');
                $model->load($id);
                $model->delete();

                Mage::getSingleton('adminhtml/session')->addSuccess(
                    Mage::helper('{namespace.lower()}_{module.lower()}')->__('{entity_class} was successfully deleted')
                );
            }} catch (Exception $e) {{
                Mage::getSingleton('adminhtml/session')->addError($e->getMessage());
                $this->_redirect('*/*/edit', ['id' => $id]);
                return;
            }}
        }}
        $this->_redirect('*/*/');
    }}

    public function massDeleteAction(): void
    {{
        $ids = $this->getRequest()->getParam('ids');
        if (!is_array($ids)) {{
            Mage::getSingleton('adminhtml/session')->addError(
                Mage::helper('{namespace.lower()}_{module.lower()}')->__('Please select item(s)')
            );
        }} else {{
            try {{
                foreach ($ids as $id) {{
                    $model = Mage::getModel('{namespace.lower()}_{module.lower()}/{entity_name}')->load($id);
                    $model->delete();
                }}
                Mage::getSingleton('adminhtml/session')->addSuccess(
                    Mage::helper('{namespace.lower()}_{module.lower()}')->__(
                        'Total of %d record(s) were successfully deleted', count($ids)
                    )
                );
            }} catch (Exception $e) {{
                Mage::getSingleton('adminhtml/session')->addError($e->getMessage());
            }}
        }}
        $this->_redirect('*/*/index');
    }}

    protected function _isAllowed(): bool
    {{
        return Mage::getSingleton('admin/session')->isAllowed(self::ADMIN_RESOURCE);
    }}
}}
"""

    controller_file.write_text(controller_content)
    files_created.append(str(controller_file))


def generate_admin_blocks(namespace, module, entity, all_entities, code_path, files_created):
    """
    Generate admin block files (Grid, Edit, Form)

    Args:
        namespace: Module namespace
        module: Module name
        entity: Entity dict with name, fields, etc
        all_entities: List of all entities (for relationships)
        code_path: Path to module root
        files_created: List to append created files to
    """
    year = datetime.now().year
    entity_name = entity['name']
    entity_class = entity_name.capitalize()
    fields = entity.get('fields', [])

    block_path = code_path / "Block" / "Adminhtml" / entity_class
    block_path.mkdir(parents=True, exist_ok=True)

    # 1. Container block
    container_file = block_path.parent / f"{entity_class}.php"
    container_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

class {namespace}_{module}_Block_Adminhtml_{entity_class} extends Mage_Adminhtml_Block_Widget_Grid_Container
{{
    public function __construct()
    {{
        $this->_controller = 'adminhtml_{entity_name}';
        $this->_blockGroup = '{namespace.lower()}_{module.lower()}';
        $this->_headerText = Mage::helper('{namespace.lower()}_{module.lower()}')->__('Manage {entity_class}');
        $this->_addButtonLabel = Mage::helper('{namespace.lower()}_{module.lower()}')->__('Add {entity_class}');
        parent::__construct();
    }}
}}
"""
    container_file.write_text(container_content)
    files_created.append(str(container_file))

    # 2. Grid block
    grid_file = block_path / "Grid.php"

    # Build grid columns from fields
    grid_columns = ""
    for field in fields:
        # Check if field should be shown in grid
        show_in_grid = field.get('admin', {}).get('grid', False)

        # Always show ID field
        if field['name'] == f"{entity_name}_id":
            show_in_grid = True

        if not show_in_grid:
            continue

        field_name = field['name']
        field_label = field.get('label', field_name.replace('_', ' ').title())
        field_type = field.get('type', 'varchar')

        # Determine column type and options
        column_config = f"""
        $this->addColumn('{field_name}', [
            'header' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('{field_label}'),"""

        if field_name == f"{entity_name}_id":
            column_config += """
            'width' => '50px',"""

        column_config += f"""
            'index' => '{field_name}',"""

        # Add type-specific config
        # Relationship fields ending in _id (except status_id)
        if field_name.endswith('_id') and field_name != f"{entity_name}_id" and field_name != 'status_id':
            related_entity = field_name[:-3]
            # Check if this entity exists in all_entities
            if any(e['name'] == related_entity for e in all_entities):
                related_class = related_entity.capitalize()
                column_config += f"""
            'type' => 'options',
            'options' => Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity}_collection')->toOptionHash(),"""
        # Boolean fields - is_, allow_, enable_, has_ prefixes or smallint
        elif field_name.startswith(('is_', 'allow_', 'enable_', 'has_')) or (field_type in ['smallint', 'tinyint'] and field_name != 'status'):
            column_config += """
            'type' => 'options',
            'options' => ['1' => 'Yes', '0' => 'No'],"""
        # Status field
        elif field_name == 'status':
            column_config += f"""
            'type' => 'options',
            'options' => {namespace}_{module}_Model_{entity_class}::getAvailableStatuses(),"""
        # Date/datetime fields
        elif field_type in ['datetime', 'timestamp']:
            column_config += """
            'type' => 'datetime',"""
        # Numeric fields
        elif field_type in ['int', 'smallint', 'bigint', 'decimal']:
            column_config += """
            'type' => 'number',"""

        column_config += """
        ]);"""

        grid_columns += column_config

    grid_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

class {namespace}_{module}_Block_Adminhtml_{entity_class}_Grid extends Mage_Adminhtml_Block_Widget_Grid
{{
    public function __construct()
    {{
        parent::__construct();
        $this->setId('{entity_name}Grid');
        $this->setDefaultSort('{entity_name}_id');
        $this->setDefaultDir('DESC');
        $this->setSaveParametersInSession(true);
        $this->setUseAjax(true);
    }}

    protected function _prepareCollection(): static
    {{
        $collection = Mage::getModel('{namespace.lower()}_{module.lower()}/{entity_name}')->getCollection();
        $this->setCollection($collection);
        return parent::_prepareCollection();
    }}

    protected function _prepareColumns(): static
    {{{grid_columns}

        $this->addColumn('action', [
            'header' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Action'),
            'width' => '50px',
            'type' => 'action',
            'getter' => 'getId',
            'actions' => [[
                'caption' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Edit'),
                'url' => ['base' => '*/*/edit'],
                'field' => 'id',
            ]],
            'filter' => false,
            'sortable' => false,
        ]);

        return parent::_prepareColumns();
    }}

    protected function _prepareMassaction(): static
    {{
        $this->setMassactionIdField('{entity_name}_id');
        $this->getMassactionBlock()->setFormFieldName('ids');

        $this->getMassactionBlock()->addItem('delete', [
            'label' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Delete'),
            'url' => $this->getUrl('*/*/massDelete'),
            'confirm' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Are you sure?'),
        ]);

        return $this;
    }}

    public function getRowUrl($row)
    {{
        return $this->getUrl('*/*/edit', ['id' => $row->getId()]);
    }}

    public function getGridUrl()
    {{
        return $this->getUrl('*/*/grid', ['_current' => true]);
    }}
}}
"""
    grid_file.write_text(grid_content)
    files_created.append(str(grid_file))

    # 3. Edit container
    edit_path = block_path / "Edit"
    edit_path.mkdir(parents=True, exist_ok=True)

    edit_file = edit_path.parent / "Edit.php"
    edit_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

class {namespace}_{module}_Block_Adminhtml_{entity_class}_Edit extends Mage_Adminhtml_Block_Widget_Form_Container
{{
    public function __construct()
    {{
        parent::__construct();

        $this->_objectId = 'id';
        $this->_blockGroup = '{namespace.lower()}_{module.lower()}';
        $this->_controller = 'adminhtml_{entity_name}';

        $this->_updateButton('save', 'label', Mage::helper('{namespace.lower()}_{module.lower()}')->__('Save {entity_class}'));
        $this->_updateButton('delete', 'label', Mage::helper('{namespace.lower()}_{module.lower()}')->__('Delete {entity_class}'));

        $this->_addButton('saveandcontinue', [
            'label' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Save and Continue Edit'),
            'onclick' => 'saveAndContinueEdit()',
            'class' => 'save',
        ], -100);

        $this->_formScripts[] = "
            function saveAndContinueEdit() {{
                editForm.submit($('edit_form').action + 'back/edit/');
            }}
        ";
    }}

    public function getHeaderText()
    {{
        if (Mage::registry('current_{entity_name}')->getId()) {{
            return Mage::helper('{namespace.lower()}_{module.lower()}')->__("Edit {entity_class}");
        }} else {{
            return Mage::helper('{namespace.lower()}_{module.lower()}')->__('New {entity_class}');
        }}
    }}
}}
"""
    edit_file.write_text(edit_content)
    files_created.append(str(edit_file))

    # 4. Form block
    form_file = edit_path / "Form.php"

    # Build form fields
    form_fields = ""
    wysiwyg_fields = []

    for field in fields:
        # Skip system fields
        if field['name'] in [f"{entity_name}_id", 'created_at', 'updated_at']:
            continue

        # Check if field should be shown in form
        show_in_form = field.get('admin', {}).get('form', True)
        if not show_in_form:
            continue

        field_name = field['name']
        field_label = field.get('label', field_name.replace('_', ' ').title())
        field_db_type = field.get('type', 'varchar')

        # Detect field type based on name and db type
        field_type = 'text'
        field_options = {}

        # WYSIWYG detection - content, description, bio fields
        if field_name in ['content', 'description', 'bio'] or (field_db_type in ['text', 'mediumtext', 'longtext'] and field_name not in ['ingredients', 'instructions']):
            field_type = 'editor'
            wysiwyg_fields.append(field_name)
            field_options['wysiwyg'] = True
            field_options['style'] = 'height:300px'
        # Image upload detection
        elif field_name in ['image', 'avatar', 'photo', 'thumbnail'] or '_image' in field_name:
            field_type = 'image'
        # Multiselect detection - fields ending in _ids (plural)
        elif field_name.endswith('_ids'):
            # Extract related entity name (category_ids -> category, tag_ids -> tag)
            related_entity = field_name[:-4]  # Remove '_ids'
            related_class = related_entity.capitalize()

            # Check if this entity exists in all_entities
            if any(e['name'] == related_entity for e in all_entities):
                field_type = 'multiselect'
                field_options['values'] = f"Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity}_collection')->toOptionArray()"
                field_options['name'] = f'{field_name}[]'
        # Relationship detection - fields ending in _id (except status_id)
        elif field_name.endswith('_id') and field_name != 'status_id':
            # Extract related entity name (author_id -> author, category_id -> category)
            related_entity = field_name[:-3]
            related_class = related_entity.capitalize()

            # Check if this entity exists in all_entities
            if any(e['name'] == related_entity for e in all_entities):
                field_type = 'select'
                field_options['values'] = f"Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity}_collection')->toOptionArray()"
        # Boolean detection - is_, allow_, enable_, has_ prefixes or smallint type
        elif field_name.startswith(('is_', 'allow_', 'enable_', 'has_')) or (field_db_type in ['smallint', 'tinyint'] and field_name != 'status'):
            field_type = 'select'
            field_options['values'] = "array(['value' => 1, 'label' => 'Yes'], ['value' => 0, 'label' => 'No'])"
        # Status field
        elif field_name == 'status':
            field_type = 'select'
            field_options['values'] = f"{namespace}_{module}_Model_{entity_class}::getAvailableStatuses()"
        # Color picker fields
        elif field_name in ['color', 'colour', 'background_color', 'text_color'] or field_name.endswith('_color'):
            field_type = 'text'
            field_options['class'] = "'jscolor {hash:true}'"
        # Email fields
        elif field_name in ['email', 'email_address'] or field_name.endswith('_email'):
            field_type = 'text'
            field_options['class'] = "'validate-email'"
        # URL fields
        elif field_name in ['url', 'link', 'website'] or field_name.endswith('_url') or field_name.endswith('_link'):
            field_type = 'text'
            field_options['class'] = "'validate-url'"
        # Price/money fields
        elif field_name in ['price', 'cost', 'amount'] or field_name.endswith('_price') or field_name.endswith('_cost'):
            field_type = 'text'
            field_options['class'] = "'validate-number'"
        # Numeric fields (int/decimal)
        elif field_db_type in ['int', 'integer', 'decimal', 'float'] and field_name not in ['status', 'position', 'sort_order']:
            field_type = 'text'
            field_options['class'] = "'validate-number'"
        # File upload detection
        elif field_name in ['file', 'attachment', 'document', 'pdf'] or field_name.endswith('_file'):
            field_type = 'file'
        # Time fields
        elif field_db_type == 'time':
            field_type = 'time'
            field_options['image'] = "$this->getSkinUrl('images/grid-cal.gif')"
            field_options['format'] = "'HH:mm:ss'"
        # Datetime fields (with time picker)
        elif field_db_type == 'datetime' or field_name.endswith('_at'):
            field_type = 'datetime'
            field_options['image'] = "$this->getSkinUrl('images/grid-cal.gif')"
            field_options['format'] = "'Y-MM-dd HH:mm:ss'"
            field_options['time'] = 'true'
        # Date fields (date only, no time)
        elif field_db_type == 'date':
            field_type = 'date'
            field_options['image'] = "$this->getSkinUrl('images/grid-cal.gif')"
            field_options['format'] = "'Y-MM-dd'"
        # Regular textarea
        elif field_db_type in ['text', 'mediumtext', 'longtext']:
            field_type = 'textarea'
            field_options['style'] = 'height:100px'

        # Get field name (may be overridden for multiselect)
        actual_field_name = field_options.get('name', f"'{field_name}'")

        form_fields += f"""
        $fieldset->addField('{field_name}', '{field_type}', [
            'name' => {actual_field_name},
            'label' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('{field_label}'),
            'title' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('{field_label}'),
            'required' => {str(not field.get('nullable', True)).lower()},"""

        # Add field-specific options
        for opt_key, opt_value in field_options.items():
            if opt_key == 'name':
                # Already handled above
                continue
            elif opt_key == 'values':
                form_fields += f"""
            '{opt_key}' => {opt_value},"""
            elif opt_key == 'wysiwyg':
                form_fields += f"""
            'wysiwyg' => true,
            'config' => Mage::getSingleton('cms/wysiwyg_config')->getConfig(),"""
            else:
                # Check if value needs quoting (strings that don't start with special chars)
                if isinstance(opt_value, str) and not opt_value.startswith(("'", '"', '$', 'Mage::', 'array(')):
                    opt_value = f"'{opt_value}'"
                form_fields += f"""
            '{opt_key}' => {opt_value},"""

        form_fields += """
        ]);"""

    # Add multistore selector if enabled
    if entity.get('multi_store', False):
        form_fields += f"""
        // Multistore selector
        if (!Mage::app()->isSingleStoreMode()) {{
            $fieldset->addField('store_id', 'multiselect', [
                'name' => 'stores[]',
                'label' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Store View'),
                'title' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Store View'),
                'required' => true,
                'values' => Mage::getSingleton('adminhtml/system_store')->getStoreValuesForForm(false, true),
            ]);
        }} else {{
            $fieldset->addField('store_id', 'hidden', [
                'name' => 'stores[]',
                'value' => Mage::app()->getStore(true)->getId(),
            ]);
        }}"""

    form_content = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 */

class {namespace}_{module}_Block_Adminhtml_{entity_class}_Edit_Form extends Mage_Adminhtml_Block_Widget_Form
{{
    protected function _prepareLayout(): static
    {{
        parent::_prepareLayout();
        if (Mage::getSingleton('cms/wysiwyg_config')->isEnabled()) {{
            if ($head = $this->getLayout()->getBlock('head')) {{
                $head->setCanLoadWysiwyg(true);
            }}
        }}
        return $this;
    }}

    protected function _prepareForm(): static
    {{
        $model = Mage::registry('current_{entity_name}');

        $form = new Varien_Data_Form([
            'id' => 'edit_form',
            'action' => $this->getUrl('*/*/save', ['id' => $this->getRequest()->getParam('id')]),
            'method' => 'post',
            'enctype' => 'multipart/form-data',
        ]);

        $form->setUseContainer(true);

        $fieldset = $form->addFieldset('base_fieldset', [
            'legend' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('{entity_class} Information'),
            'class' => 'fieldset-wide',
        ]);

        if ($model->getId()) {{
            $fieldset->addField('{entity_name}_id', 'hidden', [
                'name' => '{entity_name}_id',
            ]);
        }}{form_fields}

        $form->setValues($model->getData());
        $this->setForm($form);

        return parent::_prepareForm();
    }}
}}
"""
    form_file.write_text(form_content)
    files_created.append(str(form_file))


def generate_adminhtml_layout_handles(namespace, module, entity_name, has_wysiwyg=False):
    """
    Generate adminhtml layout XML for an entity

    Args:
        namespace: Module namespace (lowercase)
        module: Module name (lowercase)
        entity_name: Entity name (lowercase)
        has_wysiwyg: Whether entity has WYSIWYG editor fields

    Returns:
        XML string to be inserted into layout
    """
    wysiwyg_block = ""
    if has_wysiwyg:
        wysiwyg_block = """
        <update handle="editor"/>"""

    return f"""
    <adminhtml_{entity_name}_index>
        <reference name="content">
            <block type="{namespace}_{module}/adminhtml_{entity_name}" name="{entity_name}" />
        </reference>
    </adminhtml_{entity_name}_index>

    <adminhtml_{entity_name}_grid>
        <block name="root" type="{namespace}_{module}/adminhtml_{entity_name}_grid" />
    </adminhtml_{entity_name}_grid>

    <adminhtml_{entity_name}_edit>{wysiwyg_block}
        <reference name="content">
            <block type="{namespace}_{module}/adminhtml_{entity_name}_edit" name="{entity_name}.edit" />
        </reference>
    </adminhtml_{entity_name}_edit>
"""
