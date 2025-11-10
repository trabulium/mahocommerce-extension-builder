# MahoCommerce Extension Builder

**Version:** 1.0.0
**Based on:** Deep introspection of MahoCommerce (3,601 classes analyzed)

## Overview

This skill enables Claude to build MahoCommerce extensions with 100% accuracy by using patterns extracted from actual working code, not assumptions. All templates, validators, and generators are based on introspection of a live Maho installation.

## Introspection Data

This skill is built on analysis of:
- **3,601 core classes** (Mage + Maho namespaces)
- **216 controllers** (admin + frontend patterns)
- **1,336 blocks** (grids, forms, widgets)
- **1,916 models** (ORM patterns, resource models, collections)
- **133 helpers**
- **110 working grid implementations**
- **57 config.xml schemas**
- **39 adminhtml.xml patterns** (menus + ACL)
- **59 layout handles**

All data is in `analysis/` directory as JSON files.

## Key Principles

1. **NEVER GUESS** - All patterns come from actual analyzed code
2. **USE REAL EXAMPLES** - Reference implementations from Mage_Catalog, Mage_Cms, etc.
3. **VALIDATE EVERYTHING** - Check against discovered schemas before outputting
4. **INTROSPECTION-FIRST** - When in doubt, check the analysis files

## Critical Rules (From Breaking Changes Analysis)

### NEVER Use These (Removed from Maho)
- `Varien_Http_Client` → Use `Symfony\Component\HttpClient\HttpClient`
- `Varien_Http_Adapter_Curl` → Use Symfony HttpClient
- `Zend_Json` → Use `Mage::helper('core')->jsonEncode/Decode()`
- `Zend_Date` → Use native PHP `DateTime` and `Mage_Core_Model_Locale`
- `Zend_Validate` → Use `Mage::helper('core')->isValid*()` methods
- Prototype.js - Completely removed
- jQuery version conflicts - Check `analysis/javascript.json` for available version

### NEVER Edit public/index.php for BP Errors
**Critical**: If you see "Undefined constant BP" errors, DO NOT edit `public/index.php`!
- ❌ DO NOT replace `BP` with `MAHO_ROOT_DIR`
- ❌ DO NOT add `define('BP', ...)` statements
- ✅ ALWAYS run: `COMPOSER_ALLOW_SUPERUSER=1 composer dump-autoload`

The BP constant is defined by the Maho composer plugin's autoloader registration, not in code. Editing index.php breaks the bootstrap process.

### NEVER Add declare(strict_types=1) to Legacy Code
**Critical**: When porting Magento 1 extensions, DO NOT add `declare(strict_types=1)`!
- ❌ DO NOT add `declare(strict_types=1)` to files with header comments
- ❌ DO NOT blindly add strict_types to all files during conversion
- ⚠️ PHP requires `declare(strict_types=1)` to be the FIRST statement after `<?php` with NO blank lines or comments

**Problem**: Legacy Magento 1 extensions have this pattern:
```php
<?php

/**
 * File header comment
 */
class Foo {}
```

If you add `declare(strict_types=1)` after the `<?php` line, it comes BEFORE the comment, which violates PHP syntax rules and causes silent failures or grey screens.

**Only add strict_types to NEW Maho modules** where you control the file structure.

### ALWAYS Use These (From Core Classes Map)

**Controllers:**
```php
// Admin controllers
class Namespace_Module_Adminhtml_ControllerController extends Mage_Adminhtml_Controller_Action
{
    public const ADMIN_RESOURCE = 'module/resource/path'; // Required for ACL

    protected function _isAllowed()
    {
        return Mage::getSingleton('admin/session')->isAllowed(self::ADMIN_RESOURCE);
    }
}

// Frontend controllers
class Namespace_Module_ControllerController extends Mage_Core_Controller_Front_Action
{
    public function indexAction()
    {
        $this->loadLayout();
        $this->renderLayout();
    }
}
```

**Models (From 1,916 analyzed):**
```php
// Model
class Namespace_Module_Model_Entity extends Mage_Core_Model_Abstract
{
    protected function _construct()
    {
        $this->_init('module/entity');
    }
}

// Resource Model
class Namespace_Module_Model_Resource_Entity extends Mage_Core_Model_Resource_Db_Abstract
{
    protected function _construct()
    {
        $this->_init('module/entity_table', 'entity_id');
    }
}

// Collection
class Namespace_Module_Model_Resource_Entity_Collection extends Mage_Core_Model_Resource_Db_Collection_Abstract
{
    protected function _construct()
    {
        $this->_init('module/entity');
    }
}
```

**Grid Blocks (110 examples analyzed):**
```php
class Namespace_Module_Block_Adminhtml_Entity_Grid extends Mage_Adminhtml_Block_Widget_Grid
{
    protected function _prepareCollection()
    {
        $collection = Mage::getModel('module/entity')->getCollection();
        $this->setCollection($collection);
        return parent::_prepareCollection();
    }

    protected function _prepareColumns()
    {
        $this->addColumn('entity_id', [
            'header' => Mage::helper('module')->__('ID'),
            'align'  => 'right',
            'width'  => '50px',
            'index'  => 'entity_id',
        ]);

        // See analysis/admin_patterns.json for more column types
        return parent::_prepareColumns();
    }
}
```

## Routing Patterns (From 57 Config Analysis)

### Admin Routing
**Critical:** Admin routing MUST follow this exact pattern (from config_schemas analysis):

```xml
<admin>
    <routers>
        <adminhtml>
            <args>
                <modules>
                    <namespace_module before="Mage_Adminhtml">Namespace_Module_Adminhtml</namespace_module>
                </modules>
            </args>
        </adminhtml>
    </routers>
</admin>
```

**Common 404 Causes:**
1. Wrong scope: Using `<adminhtml><routers>` instead of `<admin><routers>`
2. Missing `before="Mage_Adminhtml"` attribute
3. Controller class name mismatch
4. Composer autoloader not refreshed

### Frontend Routing
```xml
<frontend>
    <routers>
        <module>
            <use>standard</use>
            <args>
                <module>Namespace_Module</module>
                <frontName>moduleroute</frontName>
            </args>
        </module>
    </routers>
</frontend>
```

## Admin Interface Patterns (From 110 Grid + 39 ACL Examples)

### Menu Registration (adminhtml.xml)
```xml
<adminhtml>
    <menu>
        <namespace_module translate="title" module="module">
            <title>Menu Title</title>
            <sort_order>100</sort_order>
            <children>
                <items translate="title">
                    <title>Manage Items</title>
                    <action>adminhtml/controller/index</action>
                    <sort_order>10</sort_order>
                </items>
            </children>
        </namespace_module>
    </menu>
</adminhtml>
```

### ACL Registration (adminhtml.xml)
```xml
<adminhtml>
    <acl>
        <resources>
            <admin>
                <children>
                    <namespace_module translate="title" module="module">
                        <title>Module Name</title>
                        <sort_order>100</sort_order>
                        <children>
                            <items translate="title">
                                <title>Manage Items</title>
                            </items>
                        </children>
                    </namespace_module>
                </children>
            </admin>
        </resources>
    </acl>
</adminhtml>
```

## Database Patterns (From Analysis)

### Table Creation (Modern Maho Pattern)
```php
$installer = $this;
$installer->startSetup();

$table = $installer->getConnection()
    ->newTable($installer->getTable('module/entity'))
    ->addColumn('entity_id', Varien_Db_Ddl_Table::TYPE_INTEGER, null, [
        'identity'  => true,
        'nullable'  => false,
        'primary'   => true,
    ], 'Entity ID')
    ->addColumn('name', Varien_Db_Ddl_Table::TYPE_VARCHAR, 255, [
        'nullable'  => false,
    ], 'Name')
    ->addColumn('status', Varien_Db_Ddl_Table::TYPE_SMALLINT, null, [
        'nullable'  => false,
        'default'   => '1',
    ], 'Status')
    ->addColumn('created_at', Varien_Db_Ddl_Table::TYPE_TIMESTAMP, null, [
        'nullable'  => false,
        'default'   => Varien_Db_Ddl_Table::TIMESTAMP_INIT,
    ], 'Created At')
    ->addColumn('updated_at', Varien_Db_Ddl_Table::TYPE_TIMESTAMP, null, [
        'nullable'  => false,
        'default'   => Varien_Db_Ddl_Table::TIMESTAMP_INIT_UPDATE,
    ], 'Updated At')
    ->addIndex(
        $installer->getIdxName('module/entity', ['status']),
        ['status']
    )
    ->setComment('Module Entity Table');

$installer->getConnection()->createTable($table);

$installer->endSetup();
```

## JavaScript Patterns (From JS Analysis)

**DO NOT USE:**
- `$()` or `$$()` - Prototype selectors
- `Event.observe()` - Prototype events
- `Ajax.Request` - Prototype AJAX

**USE INSTEAD:**
- `document.querySelector()` or jQuery
- `addEventListener()` or jQuery `.on()`
- `fetch()` API or jQuery `.ajax()`

## Extension Generation Workflow

When a user requests an extension:

### 1. Gather Requirements
Ask the user:
- Module name and namespace
- Feature type: CRUD admin, frontend controller, custom functionality
- Admin interface needed? (grid, form, both)
- Database tables needed?
- Frontend pages needed?
- Specific Maho/Magento 1 code to convert?

### 2. Interactive Design Phase - CRITICAL!

**ALWAYS analyze the requirements and make suggestions BEFORE generating the JSON config.**

For each entity, think through and suggest:

**Grid Columns:**
- "I recommend showing these fields in the admin grid: ID, Title, Published Date, Status, Author. Sound good?"
- Consider what admins need to see at a glance
- Suggest published/created dates for sorting
- Suggest status fields for filtering
- Suggest relationship fields (author, category) for quick reference

**Relationships:**
- "Should posts have an author? I can add an Author entity with FK relationship."
- "Do you want tags? I can create a Tag entity with many-to-many relationship."
- "Should posts belong to categories? I'll add Category entity with many-to-many."
- **Don't forget to ask about BOTH the FK fields AND the junction tables!**

**Multi-Store:**
- "Should this content vary by store view? I'll enable multi-store support."

**Frontend Features:**
- "Do you want category/tag filtering in the sidebar?"
- "Should the frontend show author attribution on posts?"
- "Which route should I use? (e.g., 'blog', 'news', 'articles')"

**SEO Features:**
- "I'll add URL rewrites automatically for SEO-friendly URLs like /blog/my-post-title"
- "I'll add a URL Key field that auto-generates from the title"

**Example Interactive Flow:**
```
User: "Create a blog module"

Claude: "I'll create a blog module with the following structure. Let me confirm some details:

Entities:
- Post (with title, content, excerpt, featured_image, published_at)
- Category (for organizing posts)
- Tag (for tagging posts)
- Author (for author attribution)

Relationships:
- Post -> Author (many-to-one via author_id FK)
- Post <-> Category (many-to-many)
- Post <-> Tag (many-to-many)

Admin Grid Columns for Post:
- ID, Title, Author, Published Date, Status

Frontend Features:
- SEO-friendly URLs (/blog/my-post-title)
- Category and Tag sidebar blocks
- Author attribution on post view pages

Frontend Route: 'blog' (so URLs will be /blog/...)

Does this sound good? Any changes?"

[User confirms or requests changes]

Claude: [Generates JSON config based on confirmed design]
```

**Common Mistakes to Avoid:**
- ❌ Generating JSON without asking about relationships
- ❌ Forgetting to suggest many-to-many relationships for taxonomies (categories, tags)
- ❌ Not asking which fields should appear in grids
- ❌ Missing author FK when creating content entities
- ❌ Using generic module names that conflict with core Maho modules (e.g., "Blog", "News")
- ✅ Think through the full data model and present it for approval first!

**Module Naming:**
- Avoid generic names like "Blog", "News", "FAQ" that may conflict with core Maho modules
- Use descriptive prefixes: "CompanyBlog", "ProductNews", "SupportFaq"
- Check for existing modules: `ls vendor/mahocommerce/maho/app/code/core/Maho/` before generating
- If conflict occurs, disable core module: Create `app/etc/modules/Maho_ModuleName.xml` with `<active>false</active>`

### 3. Load Relevant Analysis
```python
# Pseudocode for what Claude does
analysis = load_analysis_for_requirements(user_requirements)

if needs_admin_grid:
    grid_patterns = analysis['admin_patterns']['grid_patterns']
    grid_example = grid_patterns['examples'][0]  # Use real working example

if needs_database:
    db_patterns = analysis['database']['table_creation_examples']

if needs_routing:
    routing_schema = analysis['config_schemas']['config_xml']['routing_patterns']
```

### 3. Generate Using Real Patterns
- Don't invent XML nodes - use structures from config_schemas.json
- Don't guess class methods - use patterns from core_classes.json
- Don't assume routing works - validate against analyzed admin_patterns.json

### 4. Validate Before Output
- Check XML against discovered schemas
- Verify class inheritance matches analyzed patterns
- Confirm routing matches working examples
- Validate database column types against extracted constants

### 5. Output with Confidence
Since everything comes from introspection:
- "This routing pattern is from Mage_Catalog (analysis/config_schemas.json)"
- "Grid structure based on 110 analyzed working grids"
- "ACL format validated against 39 real adminhtml.xml files"

## Magento 1 Conversion Mode

When user provides Magento 1 code to convert:

### 1. Identify Breaking Changes
Check against breaking_changes.json:
- Removed classes
- Changed method signatures
- New required methods
- XML structure changes

### 2. Apply Conversions
**HTTP Requests:**
```php
// Magento 1
$client = new Varien_Http_Client($url);
$response = $client->request('GET');

// Maho (from introspection)
$client = \Symfony\Component\HttpClient\HttpClient::create();
$response = $client->request('GET', $url);
```

**Date Handling:**
```php
// Magento 1
$date = Mage::getModel('core/date')->date('Y-m-d');

// Maho
$date = Mage_Core_Model_Locale::today();
```

**JSON:**
```php
// Magento 1
$json = Zend_Json::encode($data);

// Maho
$json = Mage::helper('core')->jsonEncode($data);
```

### 3. Validate Converted Code
- Ensure all classes exist in core_classes.json
- Verify methods are available on target classes
- Check config.xml structure matches schema

### 4. CRITICAL: Check for Layout and Template Files
**This is the most commonly forgotten step when porting extensions!**

When copying an extension from another installation, you MUST check config.xml for layout file references and copy ALL design files:

```bash
# 1. Check config.xml for layout file references
grep -A 5 "<layout>" app/code/*/Module/etc/config.xml

# Example output:
# <layout>
#     <updates>
#         <module_name>
#             <file>path/to/layout.xml</file>  # ← Must exist in app/design!
#         </module_name>
#     </updates>
# </layout>

# 2. Find and copy ALL design files from source installation
find /source/app/design -path "*modulename*"
# Copy to: app/design/adminhtml/default/default/layout/
#      and: app/design/adminhtml/default/default/template/

# 3. Flush cache after copying
./maho cache:flush
```

**Symptoms if layout/templates are missing:**
- Grey screen / blank page
- Empty `<div id="page:main-container">` in HTML
- No errors in logs
- Admin menu loads but pages are empty

**Files to check:**
- `app/design/adminhtml/default/default/layout/*.xml` - Layout XML files
- `app/design/adminhtml/default/default/template/` - Template (.phtml) files
- `app/design/frontend/*/template/` - Frontend templates if applicable

## Troubleshooting Guide

### Admin 404 Errors

**From analysis of 216 controllers + 66 admin controllers:**

1. **Check Composer Autoloader**
   ```bash
   COMPOSER_ALLOW_SUPERUSER=1 composer dump-autoload
   ./maho cache:flush
   ```

2. **Verify Routing Config**
   - Must be in `<admin><routers><adminhtml>` (NOT `<adminhtml><routers>`)
   - Must have `before="Mage_Adminhtml"`
   - Module identifier must match controller namespace

3. **Validate Controller Location**
   - Path: `app/code/{codePool}/{Namespace}/{Module}/controllers/Adminhtml/{Controller}Controller.php`
   - Class: `{Namespace}_{Module}_Adminhtml_{Controller}Controller`
   - Extends: `Mage_Adminhtml_Controller_Action`

4. **Check ACL Permissions**
   - Defined in `etc/adminhtml.xml`
   - `_isAllowed()` method implemented
   - Admin user has role with permission

### Grid Not Showing Data

1. **Collection not prepared** - Check `_prepareCollection()` implementation
2. **Columns not added** - Verify `_prepareColumns()` has column definitions
3. **Mass actions breaking AJAX** - Ensure grid URL set correctly

## Templates Location

Ready-to-use templates based on introspection:
- `templates/config.xml.template` - Validated structure
- `templates/adminhtml.xml.template` - Menu + ACL patterns
- `templates/controller_admin.php.template` - From 66 analyzed controllers
- `templates/grid_block.php.template` - From 110 working grids
- `templates/install_script.php.template` - Database setup patterns

## Field Configuration

### Quick Reference: Choosing the Right Field Type

**When you want...**                           | **Use this type**
------------------------------------------------|------------------
Short text (names, titles, SKUs)               | `varchar`
Single-line value (prep time, servings, URLs)  | `text`
Plain text paragraph (no formatting)           | `textarea`
Rich formatted content (HTML)                  | `wysiwyg`
Numbers                                         | `int`, `smallint`, `decimal`
Dates with calendar picker                      | `date`, `datetime`, `timestamp`
Image upload                                    | `image`
Relationship to another entity                  | `int` with name ending in `_id`
Enable/Disable toggle                           | Define as `status` (auto-handled)

**Common Mistakes to Avoid:**
- ❌ Using `text` for multi-line content → Use `textarea` or `wysiwyg` instead
- ❌ Using `textarea` for short single-line fields → Use `varchar` or `text` instead
- ❌ Setting default value on TEXT columns → MySQL doesn't allow this
- ❌ Manually configuring status field → It's auto-handled, just name it `status`
- ❌ Forgetting `"grid": true` → Fields won't show in admin grid unless explicitly marked

Fields in entities support various attributes that control how they appear in the admin interface:

```json
{
  "name": "title",
  "type": "text",
  "label": "Recipe Title",
  "required": true,
  "grid": true,
  "form_tab": "general",
  "default": "1",
  "note": "Helper text shown below the field"
}
```

### Entity Attributes

**Multi-Store Support:**
- `multi_store` (boolean): Enable store view selector for this entity (default: `false`)
  - When enabled, generates:
    - `{entity}_store` junction table linking entity to stores
    - Store view multiselect in admin edit form
    - Model methods: `getStores()`, `setStores()`
    - Collection filtering by store
  - Example: `{"name": "Recipe", "multi_store": true, "fields": [...]}`

### Field Attributes

**Core Attributes:**
- `name` (required): Field database column name (e.g., `"title"`, `"status"`, `"author_id"`)
- `type` (required): Field type - see Field Types section below
- `label` (required): Human-readable label shown in forms and grids
- `required` (boolean): Whether field is required (default: `false`)

**Admin Interface:**
- `grid` (boolean): Show this field as a column in admin grid (default: `false`)
  - **Important**: Only fields with `"grid": true` will appear in the admin grid
  - By default, only ID column is shown unless you explicitly mark fields for grid display
- `form_tab` (string): Which tab this field appears on in edit form (e.g., `"general"`, `"content"`, `"details"`)

**Database:**
- `default` (string|number): Default value for the field
  - **Note**: TEXT/BLOB columns cannot have default values in MySQL
  - Safe to use with varchar, int, smallint types
- `length` (string|number): Column length (e.g., `255`, `"64k"`, `"2M"`)
- `unsigned` (boolean): For integer fields, make unsigned (default: `false`)

**UI Helpers:**
- `note` (string): Help text shown below the field in forms

### Field Types

**CRITICAL**: Field types control BOTH database column type AND form element rendering. Choose carefully!

**Single-Line Text Input** (use for: titles, names, short values):
- `varchar` - Database: VARCHAR(255), Form: single-line text input
  - Use for: Short text fields (product names, titles, SKUs)
  - Database length: 255 characters (customizable with `"length"`)
  - Example: `{"name": "title", "type": "varchar", "label": "Title"}`

**Long Text** (use for: single-line values stored as TEXT):
- `text` - Database: TEXT (64k), Form: single-line text input
  - Use for: Single values that might be long (URLs, comma-separated lists, prep_time, servings)
  - Database length: 64k
  - **Important**: Renders as SINGLE-LINE input in forms
  - Cannot have default value (MySQL TEXT limitation)
  - Example: `{"name": "prep_time", "type": "text", "label": "Prep Time"}`

**Multi-Line Text Area** (use for: plain text paragraphs):
- `textarea` - Database: TEXT, Form: multi-line textarea (no WYSIWYG)
  - Use for: Plain text that needs multiple lines (notes, summaries, metadata)
  - Renders as multi-line textarea (5-10 rows)
  - No rich text editor
  - Example: `{"name": "notes", "type": "textarea", "label": "Notes"}`

**Rich Text Editor** (use for: formatted content):
- `wysiwyg` - Database: TEXT, Form: WYSIWYG rich text editor (TinyMCE)
  - Use for: HTML content (descriptions, blog posts, product details)
  - Full rich text editor with formatting toolbar
  - Height: 36em by default
  - Example: `{"name": "description", "type": "wysiwyg", "label": "Description"}`

**Numeric:**
- `int` - Integer field
  - Form: Single-line text input
  - Database: INT (4 bytes, -2B to +2B range)
- `smallint` - Small integer (often used for boolean 0/1 or small numbers)
  - Form: Single-line text input (or select dropdown if used for flags)
  - Database: SMALLINT (2 bytes, -32k to +32k range)
- `decimal` - Decimal number (default: 12,4 precision)
  - Form: Single-line text input
  - Database: DECIMAL(12,4)

**Date/Time with Calendar Picker:**
- `date` - Database: DATE, Form: date picker with calendar popup
  - Use for: Dates without time (published_at, birth_date)
  - Form renders calendar picker widget
  - Example: `{"name": "published_at", "type": "date", "label": "Publication Date"}`
- `datetime` - Database: DATETIME, Form: date picker with time
  - Use for: Dates with time (event_starts_at)
- `timestamp` - Database: TIMESTAMP, Form: date picker
  - Use for: Auto-updating timestamps

**Special:**
- `image` - Image upload field
  - Form: File upload input with image preview
  - Database: VARCHAR(255) storing file path
  - Auto-detects fields with 'image', 'avatar', 'photo' in name
  - Note displayed: "Allowed file types: jpg, jpeg, gif, png"
  - Example: `{"name": "image", "type": "image", "label": "Product Image"}`

**Status Field (Auto-Handled):**
- The `status` field is **automatically** added as a select dropdown
- You can define it in JSON, but it will ALWAYS render as: Enabled/Disabled dropdown
- Database: SMALLINT with default value of 1
- Don't specify `type` for status - it's handled specially

**Foreign Key Fields** (relationships):
- Use `int` type with name ending in `_id` (e.g., `author_id`, `category_id`)
- Form: Automatically rendered as select dropdown with options from related entity
- Example: `{"name": "author_id", "type": "int", "label": "Author"}`
  - If `Author` entity exists, form shows dropdown with author names

### Admin Grid Columns

Grid columns are defined using the `grid` attribute, with **smart auto-detection** for primary fields:

```json
{
  "entities": [{
    "name": "Recipe",
    "fields": [
      {"name": "title", "type": "text", "label": "Recipe Title", "required": true, "grid": true},
      {"name": "description", "type": "textarea", "label": "Description", "required": false, "grid": false},
      {"name": "prep_time", "type": "text", "label": "Prep Time", "required": true, "grid": true},
      {"name": "published_at", "type": "date", "label": "Published", "required": false, "grid": true},
      {"name": "status", "type": "text", "label": "Status", "required": true, "grid": true}
    ]
  }]
}
```

**Grid Behavior:**
- ID column is **always** shown first
- **Primary display field (title or name) is AUTO-INCLUDED** even without `"grid": true`
  - This prevents the common bug where grids only show ID column
  - Example: Category entity with `name` field will always show ID + Name, even if `"grid"` not specified
- Fields with `"grid": true` appear as additional columns
- Large text fields (wysiwyg, textarea, content, description, bio) are auto-skipped even if marked for grid
- Fields are shown in the order they appear in the JSON config
- Special handling for:
  - `status` → Shows as "Enabled/Disabled" dropdown
  - `*_id` (relationship fields) → Shows as dropdown with related entity data
  - `datetime/timestamp/date` → Formatted as date/time
  - `smallint` → Shows as "Yes/No" dropdown
  - `image` fields → Shows file path

**Suggested Grid Fields:**
When designing a module, suggest these types of fields for grid display:
- Primary identifier (title/name) - auto-included
- Published/created dates - for sorting and context
- Status field - for filtering enabled/disabled items
- Foreign key relationships (author_id, category_id) - for quick reference
- Count fields (views, comments) - for metrics at a glance
- Avoid large text fields (content, description) - clutters the grid

**Example Generated Grid:**
```php
$this->addColumn('recipe_id', ['header' => 'ID', 'index' => 'recipe_id']);
$this->addColumn('title', ['header' => 'Recipe Title', 'index' => 'title']);
$this->addColumn('prep_time', ['header' => 'Prep Time', 'index' => 'prep_time']);
$this->addColumn('status', ['header' => 'Status', 'type' => 'options', 'options' => [1 => 'Enabled', 0 => 'Disabled']]);
```

## Frontend Configuration

### SEO URL Rewrites (Automatic)

**All frontend entities automatically get SEO-friendly URLs** via the Maho `core_url_rewrite` system:

**What's Generated:**
- `url_key` field automatically added to the main frontend entity (first entity in config)
- Admin form includes "URL Key" input field with auto-generation note
- Observer class that creates/updates/deletes URL rewrites on entity save/delete
- Auto-slug generation from title if URL key is left empty

**Example URL Transformation:**
```
Before: /recipe/index/view/id/1/
After:  /recipe/raghu-lamb-curry
```

**Admin Interface:**
When editing an entity, admins see:
```
URL Key: [raghu-lamb-curry]
Note: Leave empty to auto-generate from title
```

**Auto-Slug Generation:**
- "Raghu Lamb Curry" → "raghu-lamb-curry"
- Converts to lowercase
- Replaces spaces with hyphens
- Removes special characters
- Handles multiple consecutive hyphens

**Multi-Store Support:**
URL rewrites are created for each store the entity is assigned to, allowing store-specific URLs.

**Generated Files:**
- `Model/Observer.php` - Contains `create{Entity}UrlRewrite()` and `delete{Entity}UrlRewrite()` methods
- `etc/config.xml` - Registers observers for `{module}_{entity}_save_after` and `{module}_{entity}_delete_after` events
- Database installer adds `url_key` VARCHAR(255) column

**Important:**
- URL rewrites are created/updated automatically on entity save
- Changing the URL key creates a new rewrite (old URLs become 404s unless manually redirected)
- URL keys must be unique per store
- Frontend routing still requires the module's front name (e.g., `/blog/` or `/recipe/`)

### Sidebar Blocks (Config-Driven)

Sidebar blocks are **explicitly defined** in the JSON config, not auto-detected:

```json
{
  "namespace": "Company",
  "module": "Blog",
  "sidebar_blocks": ["category", "tag"],
  "sidebar_position": "right",
  "entities": [...]
}
```

**Key Points:**
- `sidebar_blocks`: Array of entity names to show as sidebar blocks (e.g., `["category", "tag", "author"]`)
- Only entities listed in `sidebar_blocks` will generate sidebar blocks
- `sidebar_position`: `"right"` or `"left"` (default: `"right"`)
- **Generic Implementation**: Works with ANY entity name, not hardcoded
- Each sidebar block uses the entity's `title` field or `name` field for display

**Generated Components:**
1. **Block Class**: `{Namespace}_{Module}_Block_{Entity}_Sidebar`
2. **Template**: `app/design/frontend/base/default/template/{namespace}/{module}/{entity}_sidebar.phtml`
3. **Layout XML**: Automatically added to `<reference name="right">` or `<reference name="left">`

**Example Templates:**
- **Tag entities**: Rendered as tag cloud with inline styling
- **Other entities**: Rendered as bulleted list

### Layout Structure

Generated modules use 2-column layout by default:
```xml
<reference name="root">
    <action method="setTemplate"><template>page/2columns-right.phtml</template></action>
</reference>
<reference name="right">
    <block type="namespace_module/category_sidebar" name="..." as="category_sidebar" template="..." />
    <block type="namespace_module/tag_sidebar" name="..." as="tag_sidebar" template="..." />
</reference>
```

**Important:** The `as` attribute is required for blocks to render!

### Breadcrumbs

Breadcrumbs are automatically added to all frontend pages:
- **List Page**: Home > {Entity Title}
- **View Page**: Home > {Entity Title} > {Item Title}

Configured in controller's `indexAction()` and `viewAction()` methods.

### Author Display

If an entity has `author_id` field AND an `Author` entity exists, author attribution is automatically shown on view pages:

```php
// Automatically generated in view template
<?php if ($item->getAuthorId()): ?>
    <?php $author = Mage::getModel('namespace_module/author')->load($item->getAuthorId()); ?>
    By <strong><?php echo $author->getName() ?></strong>
<?php endif; ?>
```

### Complete JSON Example

Here's a comprehensive example showing proper field type usage:

```json
{
  "namespace": "Company",
  "module": "Recipe",
  "entities": [
    {
      "name": "recipe",
      "label": "Recipe",
      "multi_store": true,
      "fields": [
        {
          "name": "title",
          "type": "varchar",
          "label": "Recipe Title",
          "required": true,
          "grid": true,
          "note": "Short, descriptive recipe name"
        },
        {
          "name": "slug",
          "type": "varchar",
          "label": "URL Key",
          "length": 100,
          "required": true,
          "grid": false,
          "note": "URL-friendly identifier (auto-generated if empty)"
        },
        {
          "name": "prep_time",
          "type": "text",
          "label": "Prep Time",
          "required": true,
          "grid": true,
          "note": "e.g., '30 minutes' - single-line text"
        },
        {
          "name": "cook_time",
          "type": "text",
          "label": "Cook Time",
          "required": true,
          "grid": true
        },
        {
          "name": "servings",
          "type": "text",
          "label": "Servings",
          "required": true,
          "grid": true,
          "note": "e.g., '4-6 people'"
        },
        {
          "name": "difficulty",
          "type": "text",
          "label": "Difficulty Level",
          "grid": true,
          "note": "e.g., 'Easy', 'Medium', 'Hard'"
        },
        {
          "name": "summary",
          "type": "textarea",
          "label": "Short Summary",
          "required": false,
          "grid": false,
          "note": "Plain text, no formatting (shown in listings)"
        },
        {
          "name": "description",
          "type": "wysiwyg",
          "label": "Full Description",
          "required": true,
          "grid": false,
          "note": "Rich HTML content with formatting"
        },
        {
          "name": "ingredients",
          "type": "wysiwyg",
          "label": "Ingredients List",
          "required": true,
          "grid": false
        },
        {
          "name": "instructions",
          "type": "wysiwyg",
          "label": "Cooking Instructions",
          "required": true,
          "grid": false
        },
        {
          "name": "image",
          "type": "image",
          "label": "Recipe Photo",
          "required": false,
          "grid": false
        },
        {
          "name": "author_id",
          "type": "int",
          "label": "Recipe Author",
          "required": false,
          "grid": true,
          "note": "Select from authors list"
        },
        {
          "name": "published_at",
          "type": "date",
          "label": "Publication Date",
          "required": false,
          "grid": true,
          "note": "Shows calendar picker"
        },
        {
          "name": "views_count",
          "type": "int",
          "label": "View Count",
          "default": "0",
          "grid": true,
          "note": "Number of times recipe was viewed"
        }
      ]
    },
    {
      "name": "author",
      "label": "Author",
      "fields": [
        {
          "name": "name",
          "type": "varchar",
          "label": "Author Name",
          "required": true,
          "grid": true
        },
        {
          "name": "bio",
          "type": "wysiwyg",
          "label": "Biography",
          "required": false,
          "grid": false
        },
        {
          "name": "photo",
          "type": "image",
          "label": "Profile Photo",
          "required": false,
          "grid": false
        }
      ]
    }
  ],
  "relationships": [
    {
      "type": "many_to_many",
      "left_entity": "recipe",
      "right_entity": "category"
    },
    {
      "type": "many_to_many",
      "left_entity": "recipe",
      "right_entity": "tag"
    }
  ]
}
```

**What This Generates:**
- Recipe admin with properly typed fields (single-line vs multi-line vs WYSIWYG)
- Author dropdown in Recipe form (foreign key relationship)
- Date picker for published_at field
- Image upload for recipe photo
- Many-to-many relationships with categories and tags
- Grid showing only fields marked with `"grid": true`
- Status field auto-added as Enabled/Disabled dropdown
- Store view selector (multi-store enabled for Recipe entity)
- `company_recipe_recipe_store` junction table

## Usage Examples

### Generate Simple CRUD Module
```
User: "Create a module to manage testimonials in admin"

Claude:
1. Loads admin_patterns.json for grid/form examples
2. Loads config_schemas.json for routing
3. Loads database.json for table creation
4. Generates complete module using REAL patterns
5. Validates all XML/PHP against introspection data
6. Outputs with references to source patterns
```

### Generate Module with Sidebar Blocks
```json
{
  "namespace": "Company",
  "module": "Blog",
  "sidebar_blocks": ["category", "tag"],
  "sidebar_position": "right",
  "entities": [
    {
      "name": "post",
      "fields": [
        {"name": "title", "type": "varchar"},
        {"name": "author_id", "type": "int"}
      ]
    },
    {
      "name": "category",
      "fields": [{"name": "title", "type": "varchar"}]
    },
    {
      "name": "tag",
      "fields": [{"name": "title", "type": "varchar"}]
    }
  ]
}
```

This generates:
- Category sidebar block (list style)
- Tag sidebar block (tag cloud style)
- Author attribution on posts (if Author entity exists)
- Breadcrumbs on all pages
```

### Convert Magento 1 Extension
```
User: "Convert this Magento 1 code: [pastes code]"

Claude:
1. Scans for Varien/Zend usage
2. Checks breaking_changes.json
3. Applies conversions from real Maho examples
4. Validates converted code against core_classes.json
5. Outputs with migration notes
```

## Skill Invocation

User triggers this skill by:
- "Build a Maho extension for..."
- "Create admin interface for..."
- "Convert this Magento 1 code..."
- "Generate Maho module with..."

Claude then uses this SKILL.md + all analysis/*.json files to generate accurate code.

## Success Criteria

Generated code should:
✓ Work on first try (no 404s, no errors)
✓ Follow ALL patterns from introspection
✓ Include proper ACL and permissions
✓ Have correct routing configuration
✓ Use only available classes/methods
✓ Match analyzed XML schemas exactly
✓ Reference where patterns came from

## Continuous Improvement

To update this skill when Maho changes:
```bash
cd /path/to/maho
python3 .claude/skills/mahocommerce-builder/introspect.py . .claude/skills/mahocommerce-builder
```

This re-analyzes the codebase and updates all JSON files.
