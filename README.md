# Maho Module Builder

A complete, intelligent CRUD module generator for Maho Commerce that creates production-ready modules from JSON configuration.

## What It Does

Generate complete Maho modules with:
- ✅ Full admin CRUD interface (grids, forms, controllers)
- ✅ Complete frontend (layouts, templates, controllers)
- ✅ SEO-friendly URLs with automatic rewrites
- ✅ System configuration with intelligent field suggestions
- ✅ Multi-store support built-in
- ✅ Database setup with proper migrations
- ✅ ACL permissions and admin menu
- ✅ **NEW**: Automatic deployment with composer & cache flush
- ✅ **NEW**: Force overwrite for generated modules
- ✅ **NEW**: YAML-based configuration

All from a simple JSON/YAML configuration file.

## Quick Start

### 1. Create a Configuration File

```json
{
  "module": "Blog",
  "frontend_route": "blog",
  "entities": [
    {
      "name": "post",
      "fields": [
        {"name": "title", "type": "varchar", "length": 255, "required": true},
        {"name": "content", "type": "text", "required": true},
        {"name": "url_key", "type": "varchar", "length": 255, "unique": true},
        {"name": "author_id", "type": "int"},
        {"name": "is_published", "type": "smallint", "default": 0}
      ]
    },
    {
      "name": "author",
      "fields": [
        {"name": "name", "type": "varchar", "length": 255, "required": true},
        {"name": "email", "type": "varchar", "length": 255},
        {"name": "bio", "type": "text"}
      ]
    }
  ]
}
```

### 2. Generate the Module

```bash
cd /var/www/yoursite/web
python3 .claude/skills/mahocommerce-builder/generate-module.py config.json Maho
```

That's it! The generator automatically:
- Deploys files to the web root
- Runs `composer dump-autoload`
- Flushes Maho cache

### 3. Use It

- **Admin**: Navigate to Maho → Blog in admin menu
- **Frontend**: Visit `/blog` on your site
- **Configure**: System → Configuration → General → Blog

## Configuration

The generator now supports YAML-based configuration for deployment automation. See [CONFIG.md](CONFIG.md) for full details.

**Key features:**
- Automatic deployment to web root
- Auto-run composer dump-autoload
- Auto-flush Maho cache
- Force overwrite for generated modules
- Configurable paths and behaviors

## Features

### Intelligent Code Generation

The generator understands your entity structure and creates appropriate code:

**WYSIWYG Editors**: Fields named `content`, `description`, or `bio` automatically get TipTap 3.x editor
```php
// Auto-detected in forms
if (in_array($field['name'], ['content', 'description', 'bio'])) {
    $fieldset->addField($field['name'], 'editor', [
        'config' => Mage::getSingleton('cms/wysiwyg_config')->getConfig()
    ]);
}
```

**Image Uploaders**: Fields named `image`, `photo`, or `avatar` get file upload handling
```php
// Auto-detected and handles file upload/validation
if (in_array($field['name'], ['image', 'photo', 'avatar'])) {
    // Complete upload processing with Mage_Core_Model_File_Uploader
}
```

**Relationships**: Fields ending in `_id` become dropdown selectors
```php
// author_id automatically creates dropdown
if (preg_match('/_id$/', $field['name'])) {
    $entityName = str_replace('_id', '', $field['name']);
    // Loads related entity collection for dropdown
}
```

**Boolean Fields**: `is_*` or `allow_*` fields become Yes/No dropdowns
```php
if (preg_match('/^(is_|allow_)/', $field['name'])) {
    $fieldset->addField($field['name'], 'select', [
        'values' => Mage::getSingleton('adminhtml/system_config_source_yesno')->toOptionArray()
    ]);
}
```

### Admin Interface

**Grid System**:
- Auto-detected columns based on field types
- Relationship fields show names (not IDs)
- Boolean fields as Yes/No
- Date fields with proper formatting
- Sortable and filterable
- Mass actions (delete)

**Form System**:
- Dynamic field type detection
- Inline validation rules
- Preview links for url_key fields
- Save and Continue Edit button
- Proper error handling with form data persistence

**Controllers**:
- Full CRUD operations (index, new, edit, save, delete)
- Mass delete action
- ACL permission checking
- Image upload processing
- User-friendly messages

### Frontend Scaffolding

**Clean URLs with SEO Support**:

Main entity (with url_key field):
- Pattern: `/{frontName}/{url_key}/`
- Example: `/blog/my-first-post/`
- Uses Maho's URL rewrite system

Related entities:
- Pattern: `/{frontName}/{entity}/view/id/{url_key}/`
- Example: `/blog/author/view/id/john-doe/`
- Controller-based with url_key support

**Layout System**:
- 2-column layout with right sidebar
- Breadcrumbs
- Dynamic sidebar blocks (categories, tags, recent items)
- Pagination support (10 items per page)

**Templates**:
- List view with pagination
- Detail view with full content
- Sidebar blocks automatically generated based on entity structure

### System Configuration

**Intelligent Field Suggestions**:

Analyzes your entities and suggests:
- Enable/Disable module toggle (always)
- Items per page setting (for list entities)
- Show featured images (if image fields detected)
- Show author info (if author_id field detected)
- Enable comments (if allow_comments field detected)
- SEO settings (if meta fields detected)

**Access**: System → Configuration → General → {Your Module}

### SEO-Friendly URLs

Entities with `url_key` field automatically get SEO URLs:

**How It Works**:

1. **URL Rewrite Observers**: Automatically create/update/delete URL rewrites on entity save/delete
2. **Model URL Methods**: Each model gets `getUrl()` method for clean URL generation
3. **Controller Support**: Controllers accept both numeric IDs and url_key values
4. **Multi-Store**: URL rewrites respect store context

**Generated Code**:
```php
// Model/Observer/UrlRewrite.php
public function generateRecipeUrlRewrite($observer) {
    $recipe = $observer->getEvent()->getRecipe();
    if (!$recipe->getUrlKey()) return $this;

    // Create URL rewrite: /blog/my-first-post → /blog/index/view/id/123
    Mage::getModel('core/url_rewrite')
        ->setStoreId($recipe->getStoreId())
        ->setIdPath('maho_blog/recipe/' . $recipe->getId())
        ->setRequestPath('blog/' . $recipe->getUrlKey())
        ->setTargetPath('blog/index/view/id/' . $recipe->getId())
        ->save();
}

// Model/Recipe.php
public function getUrl() {
    if ($this->getUrlKey()) {
        return Mage::getUrl('blog/' . $this->getUrlKey());
    }
    return Mage::getUrl('blog/index/view', ['id' => $this->getId()]);
}
```

### Conflict Detection

**Module Name Conflicts**:
- Checks for existing modules before generation
- Prevents accidental overwrites
- Clear error messages

**Frontend Route Conflicts**:
- Scans codebase for existing `<frontName>` routes
- Interactive prompts for alternative names
- Real-time validation of suggestions
- Non-interactive mode support via config

### Database Management

**Proper Migrations**:
```php
// sql/{namespace}_{module}_setup/25.01.01.php
$installer = $this;
$installer->startSetup();

$table = $installer->getConnection()
    ->newTable($installer->getTable('maho_blog_post'))
    ->addColumn('entity_id', Varien_Db_Ddl_Table::TYPE_INTEGER, null, [
        'identity' => true,
        'unsigned' => true,
        'nullable' => false,
        'primary'  => true,
    ], 'Entity ID')
    // ... more columns
    ->addIndex(/* proper indexes */)
    ->addForeignKey(/* relationships */)
    ->setComment('Blog Post Table');

$installer->getConnection()->createTable($table);
$installer->endSetup();
```

**Field Type Mapping**:
- `varchar` → VARCHAR with proper length
- `text` → TEXT
- `int` → INTEGER UNSIGNED
- `smallint` → SMALLINT (for status/boolean)
- `datetime` → DATETIME
- `decimal` → DECIMAL(12,4)

## Generated File Structure

```
app/code/core/{Namespace}/{Module}/
├── Block/
│   ├── Adminhtml/
│   │   ├── {Entity}.php                    # Grid container
│   │   └── {Entity}/
│   │       ├── Grid.php                    # Grid with intelligent columns
│   │       └── Edit/
│   │           ├── Form.php                # Dynamic form
│   │           └── Edit.php                # Form container
│   ├── List.php                            # Frontend list block
│   ├── View.php                            # Frontend detail block
│   └── Sidebar/                            # Auto-generated sidebar blocks
│       ├── {Entities}.php
│       └── Recent.php
├── controllers/
│   ├── Adminhtml/
│   │   └── {Entity}Controller.php          # Full CRUD + image upload
│   ├── IndexController.php                 # Frontend list/view
│   ├── {Entity}Controller.php              # Frontend entity-specific
├── etc/
│   ├── config.xml                          # Module config + URL rewrite events
│   ├── adminhtml.xml                       # ACL resources
│   └── system.xml                          # System configuration
├── Helper/
│   └── Data.php                            # Helper class
├── Model/
│   ├── {Entity}.php                        # Model with getUrl()
│   ├── Observer/
│   │   ├── UrlRewrite.php                  # URL rewrite observer
│   │   └── {Entity}UrlRewrite.php          # Entity-specific observers
│   └── Resource/
│       ├── {Entity}.php                    # Resource model
│       └── {Entity}/
│           └── Collection.php              # Collection with helpers
└── sql/{namespace}_{module}_setup/
    └── 25.01.01.php                        # Database installation

app/design/adminhtml/default/default/layout/{namespace}/{module}.xml
app/design/frontend/base/default/
├── layout/{namespace}/{module}.xml
└── template/{namespace}/{module}/
    ├── list.phtml
    ├── view.phtml
    └── sidebar/
        ├── {entities}.phtml
        └── recent.phtml

app/etc/modules/{Namespace}_{Module}.xml
```

## Configuration Options

### Basic Structure

```json
{
  "module": "ModuleName",              // Required
  "frontend_route": "route-name",      // Optional, prompts if missing
  "entities": [                        // Array of entities
    {
      "name": "entityname",            // Singular, lowercase
      "fields": [                      // Array of fields
        {
          "name": "field_name",        // Field name
          "type": "varchar",           // Field type
          "length": 255,               // For varchar
          "required": true,            // Validation
          "unique": false,             // Index
          "default": null              // Default value
        }
      ]
    }
  ]
}
```

### Field Types

| Type | Database | Form Field | Notes |
|------|----------|------------|-------|
| `varchar` | VARCHAR | text input | Specify `length` |
| `text` | TEXT | textarea or editor | Auto-detects WYSIWYG need |
| `int` | INTEGER UNSIGNED | text input | For foreign keys or numbers |
| `smallint` | SMALLINT | Yes/No dropdown | For status/boolean |
| `datetime` | DATETIME | date picker | Formatted display |
| `decimal` | DECIMAL(12,4) | text input | For prices/amounts |

### Special Field Names

| Pattern | Auto-Detection | Result |
|---------|---------------|--------|
| `content`, `description`, `bio` | WYSIWYG | TipTap 3.x editor |
| `image`, `photo`, `avatar` | File upload | Image uploader + validation |
| `*_id` | Foreign key | Dropdown with related entities |
| `is_*`, `allow_*` | Boolean | Yes/No dropdown |
| `url_key` | SEO | URL rewrite system enabled |
| `status` | Status | Enabled/Disabled dropdown |

## Usage Examples

### Blog Module

```json
{
  "module": "Blog",
  "frontend_route": "blog",
  "entities": [
    {
      "name": "post",
      "fields": [
        {"name": "title", "type": "varchar", "length": 255, "required": true},
        {"name": "url_key", "type": "varchar", "length": 255, "unique": true},
        {"name": "content", "type": "text", "required": true},
        {"name": "excerpt", "type": "text"},
        {"name": "author_id", "type": "int"},
        {"name": "category_id", "type": "int"},
        {"name": "featured_image", "type": "varchar", "length": 255},
        {"name": "published_at", "type": "datetime"},
        {"name": "is_published", "type": "smallint", "default": 0},
        {"name": "allow_comments", "type": "smallint", "default": 1}
      ]
    },
    {
      "name": "category",
      "fields": [
        {"name": "name", "type": "varchar", "length": 255, "required": true},
        {"name": "url_key", "type": "varchar", "length": 255, "unique": true},
        {"name": "description", "type": "text"}
      ]
    },
    {
      "name": "author",
      "fields": [
        {"name": "name", "type": "varchar", "length": 255, "required": true},
        {"name": "email", "type": "varchar", "length": 255},
        {"name": "bio", "type": "text"},
        {"name": "avatar", "type": "varchar", "length": 255}
      ]
    }
  ]
}
```

**What You Get**:
- Post CRUD with WYSIWYG editor for content
- Category/Author dropdowns in post form
- Featured image uploader
- Date picker for published_at
- SEO URLs: `/blog/my-first-post/`, `/blog/category/view/id/tutorials/`
- Frontend with sidebar showing categories and recent posts
- System config for items per page, comments, author display

### Recipe Module (Real Example)

See `test-recipe.json` for the complete working example that generates the Recipe module we built.

## Troubleshooting

### Admin 404 Errors

**Issue**: Menu appears but clicking gives 404

**Solutions**:
1. Run `composer dump-autoload` (most common fix)
2. Check router configuration in `etc/config.xml`
3. Verify controller class naming and location
4. Clear cache: `./maho cache:flush`
5. Check ACL permissions

### Grid Not Displaying

**Issue**: Grid page loads but shows no data

**Check**:
1. Collection is properly defined in `_prepareCollection()`
2. Store filter is applied if using store-aware entities
3. Database table exists and has data
4. Column definitions in `_prepareColumns()` match table fields

### Form Fields Not Saving

**Issue**: Form saves but field values don't persist

**Check**:
1. Field names match database columns exactly
2. Store ID is set when saving
3. Mass-action protection for store-specific fields
4. Check `saveAction()` in controller processes all fields

### SEO URLs Not Working

**Issue**: URL rewrites created but pages 404

**Check**:
1. Router is NOT registered (we don't use custom router)
2. Controller accepts url_key in 'id' parameter
3. URL rewrite observers are registered in config.xml
4. Cache is flushed after creating rewrites

## Advanced Features

### Custom Field Types

Extend field detection in `lib/admin_generator.py`:

```python
def _get_field_type_for_form(self, field):
    # Add your custom detection logic
    if field['name'].endswith('_code'):
        return 'custom_code_field'
    # ... existing logic
```

### Custom Templates

Override default templates in `lib/templates/core.py`:

```python
CUSTOM_TEMPLATE = """
<?php
// Your custom template
"""
```

### Validation Rules

Add custom validation in generated forms:

```php
$form->getElement('email')->addClass('validate-email');
$form->getElement('url')->addClass('validate-url');
```

## Development Workflow

### 1. Design Your Data Model

Think through:
- What entities do you need?
- What relationships exist?
- What fields are required?
- Do you need SEO URLs?
- Should it be store-specific?

### 2. Create JSON Config

Start simple, iterate:
```json
{
  "module": "TestModule",
  "entities": [{"name": "item", "fields": [...]}]
}
```

### 3. Generate & Test

```bash
python3 generate-module.py config.json Maho
composer dump-autoload
./maho cache:flush
```

### 4. Customize

The generated code is a starting point. Customize:
- Add custom methods to models
- Enhance forms with JavaScript
- Add custom grid columns
- Implement custom business logic

### 5. Version Control

Commit the JSON config, not just the generated code. This documents intent.

## Code Quality

### Generated Code Follows

- **PER-CS2.0** coding standards
- **PHPStan level 6** compatibility
- **Maho best practices**
- **Modern PHP 8.3+** features

### No Deprecated Code

All generated code uses:
- Current Maho classes (no Zend_*)
- Modern database layer (Doctrine DBAL)
- Up-to-date helper methods
- Latest form/grid patterns

## Performance

### Optimized Queries

- Proper collection filtering
- Index usage on foreign keys
- Efficient joins for related data
- Pagination to limit result sets

### Caching

- Uses Maho's cache system
- URL rewrites cached by core
- Collection queries cacheable
- Configuration cached

## Security

### Built-in Protection

- **XSS Prevention**: All output escaped via `escapeHtml()`
- **CSRF Protection**: Form keys on all forms
- **SQL Injection**: Parameterized queries via Doctrine
- **ACL Enforcement**: `_isAllowed()` on all admin actions
- **File Upload Validation**: Type and size checks

## Future Enhancements

- [ ] GraphQL schema generation
- [ ] REST API endpoints
- [ ] Import/Export functionality
- [ ] Sitemap.xml generation
- [ ] RSS feed generation
- [ ] Advanced search/filtering
- [ ] Many-to-many relationship support
- [ ] Cron job scaffolding
- [ ] Event/observer templates
- [ ] Custom attribute support
- [ ] Magento 1 module converter

## Requirements

- Python 3.6+
- Maho Commerce 25.x+
- PHP 8.3+
- Composer
- MySQL/MariaDB

## File Organization

```
.claude/skills/mahocommerce-builder/
├── README.md                    # This file
├── FEATURES.md                  # Detailed feature documentation
├── STATUS.md                    # Current development status
├── generate-module.py           # Main generator script
├── validate-module.php          # Module validator
├── lib/                         # Generator library
│   ├── admin_generator.py       # Admin interface generation
│   ├── frontend_generator.py   # Frontend generation
│   ├── model_generator.py       # Model layer generation
│   ├── config.py               # Configuration management
│   ├── url_rewrite_generator.py # SEO URL generation
│   ├── system_config_generator.py # System config generation
│   ├── utils.py                # Utility functions
│   └── templates/              # Code templates
│       └── core.py             # Core template definitions
├── test-recipe.json            # Example configuration
└── analysis/                   # Analysis data (deprecated)
```

## Support

For issues or questions:

1. Check FEATURES.md for detailed documentation
2. Review test-recipe.json for working examples
3. Examine generated code for patterns
4. Run with `--help` for usage information

## License

OSL 3.0 (same as Maho Commerce)

## Credits

Built with Claude Code for the Maho Commerce ecosystem.
