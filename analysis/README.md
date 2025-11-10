# Analysis Files

This directory will contain introspection data from your MahoCommerce installation.

## ⚠️ Required First Step

Before using this skill, you **must** run the introspection script to analyze your Maho installation:

```bash
cd /path/to/your/maho/installation
python3 .claude/skills/mahocommerce-builder/introspect.py . .claude/skills/mahocommerce-builder
```

## What Gets Generated

The introspection script will create these files in this directory:

- `core_classes.json` - All 3,601+ core classes with methods, inheritance, and patterns
- `admin_patterns.json` - 110 working grid examples, menu/ACL patterns
- `config_schemas.json` - 57 validated config.xml structures
- `database.json` - Database setup patterns
- `layout.json` - Layout XML patterns
- `javascript.json` - Available JS libraries
- `reference_impls.json` - Complete working module examples
- `metadata.json` - Introspection metadata and statistics

## Why Run Introspection?

This skill is **introspection-based** - it generates code by analyzing your actual MahoCommerce installation rather than guessing patterns. This ensures:

- ✅ 100% accuracy - code matches your Maho version
- ✅ No guessing - every pattern comes from working code
- ✅ Up-to-date - reflects your current installation
- ✅ Validated - generated code is checked against discovered patterns

## File Sizes

The analysis files are installation-specific and can be large:
- Total size: ~8-10 MB
- Largest: `core_classes.json` (~5.4 MB)
- `config_schemas.json` (~2 MB)
- Others: <1 MB each

## Re-running Introspection

When you update MahoCommerce, re-run introspection to keep the analysis current:

```bash
python3 .claude/skills/mahocommerce-builder/introspect.py /path/to/maho .claude/skills/mahocommerce-builder
```

## Note

These files are **gitignored** because they're specific to your installation. Each developer should generate their own analysis files.
