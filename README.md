# MahoCommerce Extension Builder & Magento 1 Converter

A Claude Code skill that builds MahoCommerce extensions with 100% accuracy using deep introspection of the actual codebase.

## ⚠️ Required First Step

**Before using this skill, you MUST run introspection on your MahoCommerce installation:**

```bash
cd /path/to/your/maho/installation
python3 .claude/skills/mahocommerce-builder/introspect.py . .claude/skills/mahocommerce-builder
```

This analyzes your installation and generates the `analysis/` files needed by the skill. Without this step, the skill cannot generate code.

## What Makes This Different?

Unlike traditional code generators that guess patterns, this skill:

1. **Analyzes Your Actual Maho Installation** - Introspects 3,600+ classes to extract real patterns
2. **Never Guesses** - Every XML node, class method, and routing pattern comes from working code
3. **Validates Everything** - Checks generated code against discovered schemas
4. **Converts Magento 1** - Intelligently migrates old code using breaking changes analysis

## Quick Start

### 1. Run Introspection (One-Time Setup)

```bash
cd /var/www/yoursite
python3 .claude/skills/mahocommerce-builder/introspect.py . .claude/skills/mahocommerce-builder
```

This analyzes your Maho installation and creates:
- `analysis/core_classes.json` - All 3,601 classes with methods, inheritance
- `analysis/admin_patterns.json` - 110 working grid examples, menu/ACL patterns
- `analysis/config_schemas.json` - 57 validated config.xml structures
- `analysis/database.json` - Database setup patterns
- `analysis/layout.json` - Layout XML patterns
- `analysis/javascript.json` - Available JS libraries
- `analysis/reference_impls.json` - Complete working modules

### 2. Using the Skill

Just ask Claude Code naturally:

```
"Build a Maho module to manage product reviews in the admin"
"Create admin CRUD interface for testimonials"
"Convert this Magento 1 extension to Maho: [paste code]"
```

Claude will:
1. Load relevant analysis files
2. Generate code using REAL patterns from your install
3. Validate against introspected schemas
4. Output working code with pattern references

## What Gets Generated

### Simple Admin CRUD

Request: *"Create module to manage blog posts"*

Generates:
```
app/code/core/Custom/Blog/
├── controllers/
│   └── Adminhtml/
│       └── PostController.php      # From analyzed admin controllers
├── Block/
│   └── Adminhtml/
│       ├── Post.php                # Container
│       └── Post/
│           ├── Grid.php            # Based on 110 grid examples
│           └── Edit/
│               └── Form.php        # From form analysis
├── Model/
│   ├── Post.php                    # Standard model pattern
│   ├── Resource/
│   │   ├── Post.php                # Resource model
│   │   └── Post/
│   │       └── Collection.php      # Collection
├── etc/
│   ├── config.xml                  # Validated routing structure
│   └── adminhtml.xml               # Menu + ACL from 39 examples
├── sql/
│   └── custom_blog_setup/
│       └── install-1.0.0.php       # Database setup patterns
└── Helper/
    └── Data.php
```

All patterns come from introspection - no guessing!

## Magento 1 Conversion

### Automatic Conversions Applied:

**HTTP Requests:**
```php
// Magento 1 (detected and flagged)
$client = new Varien_Http_Client($url);
$response = $client->request('GET');

// Auto-converted to Maho
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

### Validation

Every converted class/method is checked against `analysis/core_classes.json` to ensure it exists in Maho.

## Introspection Data

### What Gets Analyzed

**Core Classes (3,601 total):**
- 216 Controllers (admin + frontend patterns)
- 1,336 Blocks (grids, forms, widgets)
- 1,916 Models (ORM patterns)
- 133 Helpers

**Configuration:**
- 57 config.xml files (routing, modules, events)
- 39 adminhtml.xml files (menus, ACL)
- 15 layout XML files
- 59 unique layout handles

**Patterns:**
- 110 working grid implementations
- 28 menu examples
- 39 ACL patterns
- Database setup scripts

### Re-Running Introspection

When Maho updates:
```bash
python3 .claude/skills/mahocommerce-builder/introspect.py /var/www/yoursite .claude/skills/mahocommerce-builder
```

This keeps the skill accurate as Maho evolves.

## Usage Examples

### Example 1: Admin CRUD Module

```
User: "Create a testimonials module with admin grid and form"

Claude:
1. Loads admin_patterns.json → finds grid/form examples
2. Loads config_schemas.json → gets routing structure
3. Loads database.json → gets table creation patterns
4. Generates complete module:
   - Controllers with proper ACL
   - Grid with working collection
   - Form with all field types
   - Database table setup
   - Menu and permissions
5. All code references which analysis file it came from
```

### Example 2: Convert Magento 1 Code

```
User: "Convert this Magento 1 observer to Maho:"
[pastes code with Varien_Http_Client]

Claude:
1. Scans for deprecated classes
2. Checks breaking_changes.json
3. Finds Varien_Http_Client → flagged as removed
4. Looks up Symfony HttpClient pattern from javascript.json
5. Converts code with explanation
6. Validates all classes exist in core_classes.json
7. Outputs converted code + migration notes
```

### Example 3: Custom Functionality

```
User: "Add a custom field to product grid in admin"

Claude:
1. Loads admin_patterns.json
2. Finds Mage_Adminhtml_Block_Catalog_Product_Grid example
3. Shows exact _prepareColumns() pattern from analysis
4. Generates grid override with new column
5. Includes layout XML to apply override
6. References source: "Based on Mage_Catalog grid (analysis/admin_patterns.json)"
```

## Troubleshooting

### Admin 404 Errors

The skill includes troubleshooting based on analysis:

1. **Routing issue** - Validates against 57 working configs
2. **Autoloader** - Suggests `composer dump-autoload`
3. **ACL problem** - Checks against 39 ACL patterns
4. **Controller location** - Verifies against 216 controller examples

### Grid Not Working

References 110 working grids to diagnose:
- Missing `_prepareCollection()`
- Wrong column types
- Collection not set
- AJAX URL missing

## File Structure

```
.claude/skills/mahocommerce-builder/
├── README.md                   # This file
├── SKILL.md                    # Main skill orchestration
├── introspect.py              # Introspection script
├── INTROSPECTION_SUMMARY.md   # Analysis statistics
├── analysis/                   # Introspection results (JSON)
│   ├── core_classes.json
│   ├── admin_patterns.json
│   ├── config_schemas.json
│   ├── database.json
│   ├── layout.json
│   ├── javascript.json
│   ├── reference_impls.json
│   └── metadata.json
├── templates/                  # Code templates (to be created)
├── validators/                 # Validation logic (to be created)
└── generators/                 # Generation helpers (to be created)
```

## Benefits

### For Development
- ✅ Code works first time (no trial and error)
- ✅ Proper ACL and permissions from day one
- ✅ Correct routing (no admin 404s)
- ✅ Database tables use right column types
- ✅ Grids follow working patterns

### For Magento 1 Migration
- ✅ Automatic detection of breaking changes
- ✅ Intelligent code conversion
- ✅ Validation that converted code will work
- ✅ Migration notes explaining changes

### For Maintenance
- ✅ Re-run introspection when Maho updates
- ✅ Skill stays accurate as framework evolves
- ✅ New patterns automatically discovered

## Advanced Usage

### Custom Introspection

Analyze specific modules:
```python
introspector = MahoIntrospector('/var/www/site')
# Modify analyze_*() methods to focus on specific patterns
introspector.run_full_analysis()
```

### Extend Templates

Add your own templates in `templates/`:
```
templates/
├── custom_observer.php.template
├── custom_helper.php.template
└── custom_block.php.template
```

Claude will use these alongside built-in patterns.

## Requirements

- Python 3.6+
- MahoCommerce installation
- Claude Code with access to this skill

## Future Enhancements

- [ ] Visual module builder UI
- [ ] GraphQL schema generator
- [ ] API endpoint templates
- [ ] Test file generation
- [ ] Documentation auto-generation
- [ ] Extension marketplace integration

## Support

This skill is maintained as part of the MahoCommerce development workflow.

For issues:
1. Re-run introspection to ensure fresh analysis
2. Check `INTROSPECTION_SUMMARY.md` for what was found
3. Verify your Maho installation is complete

## License

Same as MahoCommerce - OSL 3.0
