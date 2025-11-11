# Maho Module Builder - Features

A complete, intelligent CRUD module generator for Maho Commerce that creates production-ready modules from JSON configuration.

## Core Features

### 1. **Declarative JSON Configuration**
- Define entire modules using simple JSON config
- Specify entities, fields, relationships in a clean format
- Automatic validation and defaults application
- Support for multiple entities per module

### 2. **Intelligent Entity Generation**

#### Database Schema
- Automatic table creation with proper Maho DDL types
- Field type mapping (varchar, text, int, smallint, datetime, decimal, bool)
- Support for field constraints (required, unique, default values)
- Auto-generated primary keys and timestamps (created_at, updated_at)
- Junction tables for many-to-many relationships

#### Model Layer
- Complete Model/Resource Model/Collection architecture
- `toOptionArray()` for form dropdowns
- `toOptionHash()` for grid filters
- Proper registry pattern implementation
- `getAvailableStatuses()` helper method

### 3. **Advanced Admin Interface**

#### Grid System
- **Intelligent Column Detection**:
  - ID column (always first)
  - Primary display field (title/name auto-detection)
  - Relationship fields as dropdowns (author_id → Author names)
  - Boolean fields as Yes/No (is_published, allow_comments)
  - Date fields with datetime formatting
  - Status column with Enabled/Disabled options
  - Action column with Edit links

- **Mass Actions**:
  - Bulk delete with confirmation
  - Extensible for custom mass actions

#### Forms
- **Dynamic Form Generation** from JSON field definitions
- **Smart Field Type Detection**:
  - Text inputs for varchar/int fields
  - Textareas for text fields
  - WYSIWYG editors (TipTap 3.x) for content/bio/description fields
  - Date pickers for datetime fields
  - Yes/No dropdowns for boolean fields
  - Image uploaders for image/avatar/photo fields
  - Relationship dropdowns (author_id → author selector)

- **WYSIWYG Integration**:
  - Automatic TipTap 3.x editor loading
  - Proper `<update handle="editor"/>` pattern
  - `setCanLoadWysiwyg(true)` configuration
  - No ID conflicts with theme elements

- **Image Upload Support**:
  - Complete file upload handling with `Mage_Core_Model_File_Uploader`
  - Automatic directory creation (`media/{namespace}_{module}/{entity}/`)
  - File validation (jpg, jpeg, gif, png)
  - Delete checkbox support
  - Proper error handling (ignores "no file" errors)

- **Form Features**:
  - ID prefixing to avoid conflicts (`{entity}_fieldname`)
  - Preview links for url_key fields
  - Save and Continue Edit button
  - Proper validation rules

#### Controllers
- Full CRUD operations (index, new, edit, save, delete)
- Mass delete action
- ACL permission checking
- Image upload processing in saveAction
- Proper error handling and user messages
- Form data persistence on errors

### 4. **System Configuration Generator**

#### Intelligent Field Suggestions
Analyzes your entities and automatically suggests relevant configuration:

- **General Settings**:
  - Enable/Disable module toggle (always included)

- **Frontend Display** (for list entities like posts, products):
  - Items per page setting
  - Show featured images toggle
  - Show author information (if author_id detected)
  - Enable comments (if allow_comments detected)

- **SEO Settings** (if meta fields detected):
  - Meta title suffix
  - Default meta description

#### Features
- Non-interactive mode (auto-uses suggestions)
- Interactive mode with 3 choices:
  1. Use all suggestions (recommended)
  2. Skip system config
  3. Customize fields (planned)
- Proper ACL integration
- Accessible at System → Configuration → General → {Module}

### 5. **Conflict Detection & Resolution**

#### Module Conflicts
- Checks for existing modules with same namespace/name
- Verifies module declaration files
- Clear error messages with recommendations
- Aborts generation to prevent overwrites

#### Frontend Route Conflicts
- Scans entire codebase for existing `<frontName>` routes
- Checks both app/code and vendor directories
- Detects conflicts with core Maho modules
- **Interactive Mode**: Prompts for alternative route name
- **Non-Interactive Mode**: Requires `frontend_route` in JSON config
- Real-time validation of alternative suggestions

### 6. **Relationship Management**

#### Auto-Detection
- Detects many-to-many patterns (post ↔ category, post ↔ tag)
- Excludes foreign key relationships (author_id)
- Common patterns: post/product/item/article with category/tag

#### Junction Tables
- Automatic creation of linking tables
- Composite primary keys
- Foreign key references
- Proper naming: `{namespace}_{module}_{entity1}_{entity2}`

### 7. **Frontend Scaffolding**

#### Router Configuration
- Standard frontend routing
- Configurable `<frontName>` with conflict detection
- Module/controller/action URL structure
- SEO-friendly URL support (see section below)

#### Controllers
- Index action (list view) with breadcrumbs
- View action (detail view) with breadcrumbs
- `noRoute` forwarding for missing items
- Registry pattern for current item
- Automatic page title setting

#### Breadcrumb Navigation
- **List Page**: Home > {Entity Title}
- **View Page**: Home > {Entity Title} > {Item Title}
- Fully integrated with Mago's breadcrumb system
- Automatic URL generation for crumb links

#### Dynamic Templates
- **List Template**:
  - Auto-detected display fields (title, excerpt, date)
  - Pagination support
  - SEO-friendly URLs for "Read More" links
  - Author attribution if entity has author_id field
- **View Template**:
  - Dynamic field rendering based on entity structure
  - Author display (if entity has author_id and Author entity exists)
  - Formatted dates
  - "Back to List" link

#### Sidebar Blocks (Auto-Generated)
- **Category Sidebar**:
  - Generated automatically if Category entity exists
  - Lists all active categories
  - Ready for category view page implementation
- **Tag Sidebar**:
  - Generated automatically if Tag entity exists
  - Tag cloud display with inline styling
  - Lists up to 20 most popular tags

#### Layout Structure
- 2-column layout with right sidebar
- Breadcrumbs block in content area
- Dynamic sidebar block inclusion based on entities
- Layout XML in `app/design/frontend/base/default/layout/`
- Templates in `app/design/frontend/base/default/template/`

### 11. **SEO-Friendly URL Support**

#### Overview
Entities with a `url_key` field automatically get SEO-friendly URL support. The module builder implements a hybrid approach that works within Maho's routing architecture.

#### URL Patterns

**Main Entity URLs** (using URL rewrites):
- Pattern: `/{frontName}/{url_key}/`
- Example: `/recipe/classic-spaghetti-carbonara/`
- Implementation: Maho's core URL rewrite system
- Works at root level because path doesn't match any controller

**Related Entity URLs** (controller-based with url_key):
- Pattern: `/{frontName}/{controller}/view/id/{url_key}/`
- Example: `/recipe/cuisine/view/id/french/`
- Example: `/recipe/author/view/id/marco-rossi/`
- Implementation: Controllers accept url_key as `id` parameter
- Necessary due to routing precedence (standard router processes these first)

#### Why the Hybrid Approach?

Maho's routing system processes URLs in this order:
1. Standard router checks if URL matches `frontName/controller/action`
2. URL rewrite router processes unmatched URLs

This means:
- `/recipe/classic-spaghetti-carbonara/` doesn't match any controller → URL rewrite works
- `/recipe/cuisine/french/` matches frontName + controller → Standard router catches it first

The solution: Controllers accept both numeric IDs and url_key values as the `id` parameter.

#### Generated Code

**Model URL Generation** (`Model/{Entity}.php`):
```php
public function getUrl(): string
{
    if ($this->getUrlKey()) {
        // Main entity uses URL rewrite
        return Mage::getUrl('{frontName}/' . $this->getUrlKey());

        // Related entities use controller URLs
        return Mage::getUrl('{frontName}/{entity}/view', ['id' => $this->getUrlKey()]);
    }
    return Mage::getUrl('{frontName}/{entity}/view', ['id' => $this->getId()]);
}
```

**Controller URL Key Support** (`controllers/{Entity}Controller.php`):
```php
public function viewAction(): void
{
    $id = $this->getRequest()->getParam('id');
    ${entity} = Mage::getModel('{alias}/{entity}');

    if ($id) {
        // Try loading by numeric ID first
        ${entity}->load($id);

        // If that didn't work, try as url_key
        if (!${entity}->getId()) {
            $collection = Mage::getResourceModel('{alias}/{entity}_collection')
                ->addFieldToFilter('url_key', $id)
                ->setPageSize(1);
            ${entity} = $collection->getFirstItem();
        }
    }

    if (!${entity}->getId()) {
        $this->norouteAction();
        return;
    }
    // ... rest of action
}
```

**URL Rewrite Observers** (`Model/Observer/UrlRewrite.php`):
```php
public function generate{Entity}UrlRewrite($observer)
{
    ${entity} = $observer->getEvent()->get{Entity}();

    if (!${entity}->getUrlKey()) {
        return $this;
    }

    // Delete old rewrites
    $collection = Mage::getResourceModel('core/url_rewrite_collection')
        ->addFieldToFilter('id_path', '{alias}/{entity}/' . ${entity}->getId());

    foreach ($collection as $rewrite) {
        $rewrite->delete();
    }

    // Create new rewrite
    Mage::getModel('core/url_rewrite')
        ->setStoreId(${entity}->getStoreId())
        ->setIdPath('{alias}/{entity}/' . ${entity}->getId())
        ->setRequestPath('{frontName}/' . ${entity}->getUrlKey())
        ->setTargetPath('{frontName}/index/view/id/' . ${entity}->getId())
        ->save();

    return $this;
}
```

**Event Registration** (`etc/config.xml`):
```xml
<events>
    <{alias}_{entity}_save_after>
        <observers>
            <{alias}_url_rewrite>
                <class>{alias}/observer_urlRewrite</class>
                <method>generate{Entity}UrlRewrite</method>
            </{alias}_url_rewrite>
        </observers>
    </{alias}_{entity}_save_after>
    <{alias}_{entity}_delete_after>
        <observers>
            <{alias}_url_rewrite_delete>
                <class>{alias}/observer_urlRewrite</class>
                <method>delete{Entity}UrlRewrite</method>
            </{alias}_url_rewrite_delete>
        </observers>
    </{alias}_{entity}_delete_after>
</events>
```

#### Block Integration

All generated blocks use model URL methods for consistency:

```php
// In List.php block
public function getItemUrl($item): string
{
    return $item->getUrl();
}

// In sidebar blocks
public function get{Entity}Url(${entity}): string
{
    return ${entity}->getUrl();
}
```

#### Benefits

1. **SEO-Friendly**: Readable URLs with keywords
2. **Backward Compatible**: Still accepts numeric IDs
3. **Consistent**: Centralized URL generation in models
4. **Automatic**: URL rewrites managed by observers
5. **Multi-Store**: Respects store context
6. **No Manual Routing**: Uses Maho's standard systems

#### Configuration Requirements

To enable SEO URLs for an entity:
1. Add `url_key` field to entity definition (type: varchar, length: 255)
2. Optionally make it unique for better SEO
3. Module builder handles all the rest automatically

### 12. **ACL & Permissions**

#### Admin Menu
- Hierarchical menu structure
- Custom menu titles and sort orders
- Icon support (planned)

#### ACL Resources
- Per-entity permissions (create, read, update, delete)
- System configuration permission
- Proper resource tree structure
- `_isAllowed()` implementation in controllers

### 13. **Code Quality**

#### Modern PHP Standards
- PHP 8.3+ compatible
- Proper namespacing for custom modules
- Type hints and return types (where applicable)
- Maho coding standards compliant

#### Best Practices
- No hardcoded values
- Dynamic field detection
- Reusable helper methods
- Proper error handling
- Session message management

#### File Organization
- Modular generator architecture
- Separate files for admin, frontend, models
- Template-based generation
- Clean separation of concerns

### 14. **Developer Experience**

#### Interactive Prompts
- Namespace selection (with validation)
- Frontend route conflict resolution
- System config field confirmation

#### Clear Feedback
- Step-by-step generation progress
- Conflict warnings with solutions
- Success confirmations
- File count reporting

#### Non-Interactive Support
- Works seamlessly when called by AI/scripts
- JSON-driven configuration
- Sensible defaults for all options

## Generated File Structure

```
app/code/{pool}/{Namespace}/{Module}/
├── Block/
│   └── Adminhtml/
│       ├── {Entity}.php (Grid Container)
│       └── {Entity}/
│           ├── Grid.php (Grid with intelligent columns)
│           └── Edit/
│               ├── Form.php (Dynamic form with smart fields)
│               └── Edit.php (Form Container)
├── controllers/
│   ├── Adminhtml/
│   │   └── {Entity}Controller.php (Full CRUD + image upload)
│   └── IndexController.php (Frontend)
├── etc/
│   ├── config.xml (Module configuration)
│   ├── adminhtml.xml (ACL resources)
│   └── system.xml (System configuration)
├── Helper/
│   └── Data.php (Helper class)
├── Model/
│   ├── {Entity}.php (Model)
│   └── Resource/
│       ├── {Entity}.php (Resource Model)
│       ├── {Entity}/
│       │   └── Collection.php (with toOptionArray & toOptionHash)
│       └── Setup.php (Database setup)
└── sql/{namespace}_{module}_setup/
    └── 25.01.01.php (Database installation script)

app/design/adminhtml/default/default/
└── layout/{namespace}/
    └── {module}.xml (Admin layout)

app/design/frontend/base/default/
├── layout/{namespace}/
│   └── {module}.xml (Frontend layout)
└── template/{namespace}/{module}/
    ├── list.phtml
    └── view.phtml

app/etc/modules/
└── {Namespace}_{Module}.xml (Module declaration)
```

## Usage Examples

### Basic Blog Module
```json
{
  "module": "Blog",
  "frontend_route": "our-blog",
  "entities": [
    {
      "name": "post",
      "fields": [
        {"name": "title", "type": "varchar", "length": 255, "required": true},
        {"name": "content", "type": "text", "required": true},
        {"name": "author_id", "type": "int"},
        {"name": "is_published", "type": "smallint", "default": 0}
      ]
    }
  ]
}
```

### Advanced Features Detected
- **WYSIWYG**: `content` field automatically gets TipTap editor
- **Relationships**: `author_id` becomes dropdown in form
- **Booleans**: `is_published` becomes Yes/No dropdown
- **Grid**: Shows Title, Author (with names), Is Published (Yes/No), Status, Created At
- **System Config**: Suggests enable toggle, pagination, author display, SEO settings

## Installation Steps

1. Run generator: `python generate-module.py config.json {Namespace}`
2. Update autoloader: `composer dump-autoload`
3. Flush cache: `./maho cache:flush`
4. Access admin menu: Admin → {Module}
5. Configure: System → Configuration → {Module}

## Planned Enhancements

### System Configuration
- [ ] Custom field addition in interactive mode
- [ ] Field reordering
- [ ] Conditional field dependencies
- [ ] Multi-select options

### Frontend
- [x] Complete frontend controllers (post view, category view, tag view)
- [x] SEO-friendly URL rewrites
- [x] Pagination implementation
- [x] Template rendering with actual data
- [x] Breadcrumbs

### Additional Features
- [ ] Sitemap.xml generation
- [ ] Cron job support
- [ ] RSS feed generation
- [ ] Comment system integration
- [ ] Search/filtering in frontend
- [ ] Import/Export functionality
- [ ] REST API endpoints

### Code Generation
- [ ] PHPUnit test scaffolding
- [ ] Integration test templates
- [ ] GraphQL schema generation
- [ ] API documentation generation

## Technical Details

### Dependencies
- Python 3.x
- Maho Commerce 25.x
- Composer (for autoloading)

### Compatibility
- Maho 25.x and above
- PHP 8.3+
- Modern browsers for admin (no IE support)

### Database
- Uses Doctrine DBAL via Maho
- Supports MySQL/MariaDB
- Proper transaction handling
- Safe schema updates

### Security
- XSS prevention (proper escaping)
- CSRF protection (form keys)
- ACL enforcement
- File upload validation
- SQL injection prevention (parameterized queries)

## Credits

Built for Maho Commerce using proven architectural patterns and best practices from the Magento/OpenMage/Maho ecosystem.

**Generated with**: Claude Code
**License**: OSL 3.0 (to match Maho)
