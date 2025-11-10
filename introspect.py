#!/usr/bin/env python3
"""
MahoCommerce Deep Introspection Tool

Analyzes a live Maho installation to extract all patterns,
schemas, and implementation details needed for accurate
extension generation.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse

class MahoIntrospector:
    def __init__(self, maho_root: Path, verbose: bool = False):
        self.maho_root = Path(maho_root)
        self.core_path = self.maho_root / 'vendor' / 'mahocommerce' / 'maho' / 'app' / 'code' / 'core' / 'Mage'
        self.app_core_path = self.maho_root / 'app' / 'code' / 'core' / 'Maho'
        self.results = {}
        self.verbose = verbose

    def log(self, message: str):
        """Print if verbose mode enabled"""
        if self.verbose:
            print(f"[INFO] {message}")

    def run_full_analysis(self):
        """Run all analysis modules"""
        print("Starting deep introspection of MahoCommerce...")
        print(f"Maho root: {self.maho_root}")
        print(f"Core path: {self.core_path}")

        self.results['metadata'] = {
            'maho_root': str(self.maho_root),
            'core_path': str(self.core_path),
            'app_core_path': str(self.app_core_path)
        }

        print("\n[1/7] Analyzing core classes...")
        self.results['core_classes'] = self.analyze_core_classes()

        print("[2/7] Analyzing configuration schemas...")
        self.results['config_schemas'] = self.analyze_config_schemas()

        print("[3/7] Analyzing admin patterns...")
        self.results['admin_patterns'] = self.analyze_admin_patterns()

        print("[4/7] Analyzing JavaScript...")
        self.results['javascript'] = self.analyze_javascript()

        print("[5/7] Analyzing database patterns...")
        self.results['database'] = self.analyze_database_patterns()

        print("[6/7] Analyzing layout patterns...")
        self.results['layout'] = self.analyze_layout_patterns()

        print("[7/7] Extracting reference implementations...")
        self.results['reference_impls'] = self.extract_reference_implementations()

        print("\n✓ Introspection complete!")
        return self.results

    def analyze_core_classes(self) -> Dict:
        """
        Walk through core classes and build complete inheritance map
        """
        classes = {
            'controllers': {},
            'blocks': {},
            'models': {},
            'helpers': {},
            'statistics': {'total': 0, 'by_type': {}}
        }

        # Analyze Mage core
        if self.core_path.exists():
            self.log(f"Scanning Mage core: {self.core_path}")
            for php_file in self.core_path.rglob('*.php'):
                analysis = self.analyze_php_file(php_file, 'Mage')
                if analysis:
                    category = self.categorize_class(analysis)
                    if category:
                        classes[category][analysis['class_name']] = analysis
                        classes['statistics']['total'] += 1
                        classes['statistics']['by_type'][category] = classes['statistics']['by_type'].get(category, 0) + 1

        # Analyze Maho core
        if self.app_core_path.exists():
            self.log(f"Scanning Maho core: {self.app_core_path}")
            for php_file in self.app_core_path.rglob('*.php'):
                analysis = self.analyze_php_file(php_file, 'Maho')
                if analysis:
                    category = self.categorize_class(analysis)
                    if category:
                        classes[category][analysis['class_name']] = analysis
                        classes['statistics']['total'] += 1
                        classes['statistics']['by_type'][category] = classes['statistics']['by_type'].get(category, 0) + 1

        self.log(f"Found {classes['statistics']['total']} classes")
        return classes

    def analyze_php_file(self, file_path: Path, namespace: str) -> Optional[Dict]:
        """
        Extract class definition, methods, properties, extends, implements
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            self.log(f"Error reading {file_path}: {e}")
            return None

        # Extract class name
        class_match = re.search(r'class\s+(\w+)(\s+extends\s+([\w\\]+))?(\s+implements\s+([\w,\s\\]+))?', content)
        if not class_match:
            return None

        class_name = class_match.group(1)
        extends = class_match.group(3)
        implements = class_match.group(5)

        # Extract methods
        methods = []
        for match in re.finditer(r'(public|protected|private)(\s+static)?\s+function\s+(\w+)\s*\((.*?)\)', content, re.DOTALL):
            methods.append({
                'visibility': match.group(1),
                'static': bool(match.group(2)),
                'name': match.group(3),
                'parameters': match.group(4).strip()
            })

        # Extract properties
        properties = []
        for match in re.finditer(r'(public|protected|private)(\s+static)?\s+\$(\w+)', content):
            properties.append({
                'visibility': match.group(1),
                'static': bool(match.group(2)),
                'name': match.group(3)
            })

        # Look for various indicators
        deprecated = bool(re.search(r'@deprecated', content))
        has_override = bool(re.search(r'#\[\\?Override\]', content))

        try:
            relative_path = str(file_path.relative_to(self.maho_root))
        except:
            relative_path = str(file_path)

        return {
            'class_name': class_name,
            'file_path': relative_path,
            'namespace': namespace,
            'extends': extends,
            'implements': [i.strip() for i in implements.split(',')] if implements else [],
            'methods': methods,
            'properties': properties,
            'deprecated': deprecated,
            'has_override_attribute': has_override,
            'abstract': 'abstract class' in content or 'abstract  class' in content,
            'interface': 'interface ' + class_name in content,
            'has_strict_types': 'declare(strict_types=1)' in content
        }

    def categorize_class(self, analysis: Dict) -> Optional[str]:
        """Determine what type of class this is"""
        class_name = analysis['class_name']
        file_path = analysis['file_path']

        if 'controller' in file_path.lower():
            return 'controllers'
        elif 'Block' in file_path or class_name.endswith('Block'):
            return 'blocks'
        elif 'Model' in file_path:
            return 'models'
        elif 'Helper' in file_path:
            return 'helpers'

        return None

    def analyze_config_schemas(self) -> Dict:
        """
        Analyze all config.xml files in core to extract valid XML structure
        """
        schemas = {
            'config_xml': {},
            'adminhtml_xml': {},
            'system_xml': {},
            'common_patterns': {}
        }

        # Find all config.xml files in both Mage and Maho
        config_files = []
        if self.core_path.exists():
            config_files.extend(self.core_path.rglob('config.xml'))
        if self.app_core_path.exists():
            config_files.extend(self.app_core_path.rglob('config.xml'))

        for config_file in config_files:
            try:
                tree = ET.parse(config_file)
                root = tree.getroot()

                schema = self.build_schema_from_xml(root)
                module_name = self.extract_module_from_path(config_file)

                schemas['config_xml'][module_name] = {
                    'file': str(config_file.relative_to(self.maho_root)) if config_file.is_relative_to(self.maho_root) else str(config_file),
                    'schema': schema
                }
            except Exception as e:
                self.log(f"Error parsing {config_file}: {e}")

        # Analyze adminhtml.xml files
        adminhtml_files = []
        if self.core_path.exists():
            adminhtml_files.extend(self.core_path.rglob('adminhtml.xml'))
        if self.app_core_path.exists():
            adminhtml_files.extend(self.app_core_path.rglob('adminhtml.xml'))

        for adminhtml_file in adminhtml_files:
            try:
                tree = ET.parse(adminhtml_file)
                root = tree.getroot()

                module_name = self.extract_module_from_path(adminhtml_file)
                schemas['adminhtml_xml'][module_name] = {
                    'file': str(adminhtml_file.relative_to(self.maho_root)) if adminhtml_file.is_relative_to(self.maho_root) else str(adminhtml_file),
                    'schema': self.build_schema_from_xml(root)
                }
            except Exception as e:
                self.log(f"Error parsing {adminhtml_file}: {e}")

        self.log(f"Analyzed {len(schemas['config_xml'])} config.xml files")
        self.log(f"Analyzed {len(schemas['adminhtml_xml'])} adminhtml.xml files")

        return schemas

    def build_schema_from_xml(self, element: ET.Element, max_depth: int = 5, current_depth: int = 0) -> Dict:
        """Recursively build schema from XML element"""
        if current_depth >= max_depth:
            return {'_truncated': True}

        schema = {
            'tag': element.tag,
            'attributes': dict(element.attrib),
            'text': element.text.strip() if element.text and element.text.strip() else None,
            'children': {}
        }

        for child in element:
            child_tag = child.tag
            if child_tag not in schema['children']:
                schema['children'][child_tag] = []

            schema['children'][child_tag].append(
                self.build_schema_from_xml(child, max_depth, current_depth + 1)
            )

        return schema

    def extract_module_from_path(self, file_path: Path) -> str:
        """Extract module name from file path"""
        parts = file_path.parts

        # Try to find Mage_ or Maho_ pattern
        for i, part in enumerate(parts):
            if part in ('Mage', 'Maho') and i + 1 < len(parts):
                return f"{part}_{parts[i+1]}"

        return str(file_path.stem)

    def analyze_admin_patterns(self) -> Dict:
        """
        Deep dive into Mage_Adminhtml module and Maho admin modules
        """
        patterns = {
            'controllers': {},
            'blocks': {},
            'menu_examples': {},
            'acl_examples': {},
            'grid_patterns': {'examples': []},
            'form_patterns': {'examples': []}
        }

        # Analyze Mage_Adminhtml
        adminhtml_path = self.core_path / 'Adminhtml' if self.core_path.exists() else None
        if adminhtml_path and adminhtml_path.exists():
            self.log(f"Analyzing Mage_Adminhtml: {adminhtml_path}")

            # Analyze controllers
            controllers_path = adminhtml_path / 'controllers'
            if controllers_path.exists():
                for controller in controllers_path.rglob('*.php'):
                    analysis = self.analyze_controller_file(controller)
                    if analysis:
                        patterns['controllers'][analysis['name']] = analysis

            # Analyze grid blocks
            grid_base = adminhtml_path / 'Block' / 'Widget' / 'Grid.php'
            if grid_base.exists():
                patterns['grid_patterns']['base_class'] = self.analyze_php_file(grid_base, 'Mage')

        # Find grid implementations across all modules
        grid_files = []
        if self.core_path.exists():
            grid_files.extend(self.core_path.rglob('*Grid.php'))
        if self.app_core_path.exists():
            grid_files.extend(self.app_core_path.rglob('*Grid.php'))

        for grid_file in grid_files:
            if 'Block' in str(grid_file) and 'Widget' not in str(grid_file):
                impl = self.analyze_grid_implementation(grid_file)
                if impl:
                    patterns['grid_patterns']['examples'].append(impl)

        self.log(f"Found {len(patterns['grid_patterns']['examples'])} grid examples")

        # Extract menu and ACL from adminhtml.xml files
        adminhtml_files = []
        if self.core_path.exists():
            adminhtml_files.extend(self.core_path.rglob('adminhtml.xml'))
        if self.app_core_path.exists():
            adminhtml_files.extend(self.app_core_path.rglob('adminhtml.xml'))

        for adminhtml_xml in adminhtml_files:
            try:
                module = self.extract_module_from_path(adminhtml_xml)
                tree = ET.parse(adminhtml_xml)
                root = tree.getroot()

                # Extract menu
                menu_node = root.find('.//menu')
                if menu_node is not None:
                    patterns['menu_examples'][module] = self.xml_to_dict(menu_node)

                # Extract ACL
                acl_node = root.find('.//acl')
                if acl_node is not None:
                    patterns['acl_examples'][module] = self.xml_to_dict(acl_node)
            except Exception as e:
                self.log(f"Error parsing {adminhtml_xml}: {e}")

        self.log(f"Found {len(patterns['menu_examples'])} menu examples")
        self.log(f"Found {len(patterns['acl_examples'])} ACL examples")

        return patterns

    def analyze_controller_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a controller file for common patterns"""
        analysis = self.analyze_php_file(file_path, 'Mage')
        if not analysis:
            return None

        analysis['type'] = 'admin' if 'Adminhtml' in str(file_path) else 'frontend'
        analysis['name'] = file_path.stem

        return analysis

    def analyze_grid_implementation(self, file_path: Path) -> Optional[Dict]:
        """Extract patterns from a grid implementation"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract prepareCollection method
            prepare_collection = re.search(
                r'protected function _prepareCollection\(\)(.*?)(?=\n    \w+\s+function|\n})',
                content,
                re.DOTALL
            )

            # Extract prepareColumns method
            prepare_columns = re.search(
                r'protected function _prepareColumns\(\)(.*?)(?=\n    \w+\s+function|\n})',
                content,
                re.DOTALL
            )

            return {
                'file': str(file_path.relative_to(self.maho_root)) if file_path.is_relative_to(self.maho_root) else str(file_path),
                'has_prepare_collection': bool(prepare_collection),
                'has_prepare_columns': bool(prepare_columns),
                'prepare_collection_snippet': prepare_collection.group(1)[:500] if prepare_collection else None,
                'prepare_columns_snippet': prepare_columns.group(1)[:500] if prepare_columns else None
            }
        except Exception as e:
            self.log(f"Error analyzing grid {file_path}: {e}")
            return None

    def xml_to_dict(self, element: ET.Element) -> Dict:
        """Convert XML element to dictionary"""
        result = {
            'tag': element.tag,
            'attributes': dict(element.attrib),
            'text': element.text.strip() if element.text and element.text.strip() else None,
            'children': []
        }

        for child in element:
            result['children'].append(self.xml_to_dict(child))

        return result

    def analyze_javascript(self) -> Dict:
        """
        Scan js/ directory for available libraries and patterns
        """
        js_path = self.maho_root / 'public' / 'js'

        analysis = {
            'libraries': [],
            'removed_libraries': [],
            'admin_js_patterns': [],
            'base_path': str(js_path)
        }

        if not js_path.exists():
            js_path = self.maho_root / 'js'
            analysis['base_path'] = str(js_path)

        if not js_path.exists():
            self.log("JS directory not found")
            return analysis

        # Check for Prototype
        if (js_path / 'prototype').exists():
            analysis['removed_libraries'].append({'name': 'Prototype.js', 'status': 'PRESENT - should be removed'})
        else:
            analysis['removed_libraries'].append({'name': 'Prototype.js', 'status': 'correctly removed'})

        # Check for jQuery
        jquery_files = list(js_path.rglob('jquery*.js'))
        if jquery_files:
            analysis['libraries'].append({
                'name': 'jQuery',
                'files': [str(f.relative_to(self.maho_root)) for f in jquery_files[:5]]  # Limit to 5
            })

        # Find mage and varien JS
        for pattern in ['mage', 'varien', 'admin']:
            files = list(js_path.rglob(f'{pattern}*.js'))
            if files:
                analysis['libraries'].append({
                    'name': pattern,
                    'count': len(files),
                    'examples': [str(f.relative_to(self.maho_root)) for f in files[:3]]
                })

        self.log(f"Found {len(analysis['libraries'])} JS library groups")

        return analysis

    def analyze_database_patterns(self) -> Dict:
        """
        Analyze all install-*.php and upgrade-*.php scripts
        """
        patterns = {
            'setup_scripts': [],
            'table_creation_examples': [],
            'common_table_patterns': {},
            'statistics': {'install_scripts': 0, 'upgrade_scripts': 0}
        }

        # Find all SQL setup scripts
        setup_dirs = []
        if self.core_path.exists():
            setup_dirs.extend(self.core_path.rglob('sql'))
        if self.app_core_path.exists():
            setup_dirs.extend(self.app_core_path.rglob('sql'))

        for sql_dir in setup_dirs:
            if sql_dir.is_dir():
                # Find install scripts
                for install_script in sql_dir.glob('*install*.php'):
                    example = self.extract_db_setup_pattern(install_script)
                    if example:
                        patterns['table_creation_examples'].append(example)
                        patterns['statistics']['install_scripts'] += 1

                # Find upgrade scripts
                for upgrade_script in sql_dir.glob('*upgrade*.php'):
                    patterns['statistics']['upgrade_scripts'] += 1

        self.log(f"Found {patterns['statistics']['install_scripts']} install scripts")
        self.log(f"Found {patterns['statistics']['upgrade_scripts']} upgrade scripts")

        return patterns

    def extract_db_setup_pattern(self, script_path: Path) -> Optional[Dict]:
        """Extract database setup patterns from a script"""
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find table creation calls
            table_creations = re.findall(
                r'\$installer->getConnection\(\)->newTable\([^)]+\)',
                content
            )

            # Find addColumn calls
            add_columns = re.findall(
                r'->addColumn\((.*?)\)',
                content,
                re.DOTALL
            )

            return {
                'file': str(script_path.relative_to(self.maho_root)) if script_path.is_relative_to(self.maho_root) else str(script_path),
                'table_count': len(table_creations),
                'column_count': len(add_columns),
                'has_foreign_keys': 'addForeignKey' in content,
                'has_indexes': 'addIndex' in content,
                'snippet': content[:1000]
            }
        except Exception as e:
            self.log(f"Error analyzing DB script {script_path}: {e}")
            return None

    def analyze_layout_patterns(self) -> Dict:
        """
        Analyze layout XML files
        """
        patterns = {
            'handle_examples': {},
            'block_type_usage': defaultdict(int),
            'action_method_usage': defaultdict(int),
            'statistics': {'layout_files': 0}
        }

        # Find all layout XML files
        layout_dirs = []
        if self.maho_root.exists():
            layout_dirs.extend((self.maho_root / 'app' / 'design').rglob('layout'))

        for layout_dir in layout_dirs:
            if layout_dir.is_dir():
                for layout_xml in layout_dir.glob('*.xml'):
                    try:
                        tree = ET.parse(layout_xml)
                        root = tree.getroot()

                        patterns['statistics']['layout_files'] += 1

                        # Extract handles
                        for handle in root:
                            if handle.tag not in ['layout', 'config']:
                                handle_name = handle.tag
                                if handle_name not in patterns['handle_examples']:
                                    patterns['handle_examples'][handle_name] = {
                                        'file': str(layout_xml.relative_to(self.maho_root)),
                                        'blocks': []
                                    }

                                # Count block types
                                for block in handle.iter('block'):
                                    block_type = block.get('type', 'unknown')
                                    patterns['block_type_usage'][block_type] += 1

                                    if len(patterns['handle_examples'][handle_name]['blocks']) < 3:
                                        patterns['handle_examples'][handle_name]['blocks'].append({
                                            'type': block_type,
                                            'name': block.get('name', ''),
                                            'template': block.get('template', '')
                                        })

                                # Count action methods
                                for action in handle.iter('action'):
                                    method = action.get('method', 'unknown')
                                    patterns['action_method_usage'][method] += 1
                    except Exception as e:
                        self.log(f"Error parsing layout {layout_xml}: {e}")

        # Convert defaultdicts to regular dicts for JSON serialization
        patterns['block_type_usage'] = dict(patterns['block_type_usage'])
        patterns['action_method_usage'] = dict(patterns['action_method_usage'])

        self.log(f"Analyzed {patterns['statistics']['layout_files']} layout files")
        self.log(f"Found {len(patterns['handle_examples'])} unique handles")

        return patterns

    def extract_reference_implementations(self) -> List[Dict]:
        """
        Extract complete, working modules as reference
        """
        reference_modules = ['Cms', 'Catalog', 'Customer', 'Sales']
        implementations = []

        for module in reference_modules:
            # Try both Mage and Maho
            module_paths = []
            if self.core_path.exists():
                module_paths.append(self.core_path / module)
            if self.app_core_path.exists():
                maho_module = self.app_core_path / module.replace('Mage_', '')
                if maho_module.exists():
                    module_paths.append(maho_module)

            for module_path in module_paths:
                if module_path.exists():
                    self.log(f"Extracting reference implementation: {module}")
                    impl = self.extract_module_structure(module_path)
                    implementations.append({
                        'module': module,
                        'path': str(module_path.relative_to(self.maho_root)) if module_path.is_relative_to(self.maho_root) else str(module_path),
                        'structure': impl
                    })
                    break  # Only need one implementation per module

        self.log(f"Extracted {len(implementations)} reference implementations")
        return implementations

    def extract_module_structure(self, module_path: Path) -> Dict:
        """Extract complete module structure"""
        structure = {
            'directories': [],
            'files': {},
            'controllers_count': 0,
            'models_count': 0,
            'blocks_count': 0,
            'helpers_count': 0
        }

        for item in module_path.rglob('*'):
            if item.is_dir():
                structure['directories'].append(str(item.relative_to(module_path)))
            else:
                rel_path = str(item.relative_to(module_path))

                # Count by type
                if 'controllers' in rel_path:
                    structure['controllers_count'] += 1
                elif 'Model' in rel_path:
                    structure['models_count'] += 1
                elif 'Block' in rel_path:
                    structure['blocks_count'] += 1
                elif 'Helper' in rel_path:
                    structure['helpers_count'] += 1

                # Store file info
                structure['files'][rel_path] = {
                    'size': item.stat().st_size,
                    'extension': item.suffix
                }

        return structure

    def save_results(self, output_dir: Path):
        """Save all analysis to JSON files"""
        output_dir = Path(output_dir)
        analysis_dir = output_dir / 'analysis'
        analysis_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving analysis to {analysis_dir}")

        for key, data in self.results.items():
            output_file = analysis_dir / f'{key}.json'
            try:
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"✓ Saved {output_file.name}")
            except Exception as e:
                print(f"✗ Error saving {output_file.name}: {e}")

        # Create summary file
        summary_file = output_dir / 'INTROSPECTION_SUMMARY.md'
        with open(summary_file, 'w') as f:
            f.write("# MahoCommerce Introspection Summary\n\n")
            f.write(f"**Maho Root:** `{self.maho_root}`\n\n")
            f.write(f"**Generated:** {self.results.get('metadata', {})}\n\n")
            f.write("## Statistics\n\n")

            if 'core_classes' in self.results:
                stats = self.results['core_classes'].get('statistics', {})
                f.write(f"- **Total Classes:** {stats.get('total', 0)}\n")
                f.write(f"- **By Type:** {stats.get('by_type', {})}\n\n")

            if 'config_schemas' in self.results:
                f.write(f"- **Config Files:** {len(self.results['config_schemas'].get('config_xml', {}))}\n")
                f.write(f"- **Adminhtml Files:** {len(self.results['config_schemas'].get('adminhtml_xml', {}))}\n\n")

            if 'admin_patterns' in self.results:
                admin = self.results['admin_patterns']
                f.write(f"- **Controllers:** {len(admin.get('controllers', {}))}\n")
                f.write(f"- **Grid Examples:** {len(admin.get('grid_patterns', {}).get('examples', []))}\n")
                f.write(f"- **Menu Examples:** {len(admin.get('menu_examples', {}))}\n")
                f.write(f"- **ACL Examples:** {len(admin.get('acl_examples', {}))}\n\n")

            if 'database' in self.results:
                db_stats = self.results['database'].get('statistics', {})
                f.write(f"- **Install Scripts:** {db_stats.get('install_scripts', 0)}\n")
                f.write(f"- **Upgrade Scripts:** {db_stats.get('upgrade_scripts', 0)}\n\n")

            if 'layout' in self.results:
                layout_stats = self.results['layout'].get('statistics', {})
                f.write(f"- **Layout Files:** {layout_stats.get('layout_files', 0)}\n")
                f.write(f"- **Unique Handles:** {len(self.results['layout'].get('handle_examples', {}))}\n\n")

            f.write("## Files Generated\n\n")
            for key in self.results.keys():
                f.write(f"- `analysis/{key}.json`\n")

        print(f"✓ Saved {summary_file.name}")


def main():
    parser = argparse.ArgumentParser(
        description='Deep introspection of MahoCommerce installation'
    )
    parser.add_argument(
        'maho_root',
        help='Path to Maho installation root'
    )
    parser.add_argument(
        'output_dir',
        help='Directory to save analysis results'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Validate Maho root
    maho_root = Path(args.maho_root)
    if not maho_root.exists():
        print(f"Error: Maho root does not exist: {maho_root}")
        return 1

    # Run introspection
    introspector = MahoIntrospector(maho_root, verbose=args.verbose)
    introspector.run_full_analysis()
    introspector.save_results(args.output_dir)

    print("\n" + "="*60)
    print("Introspection complete!")
    print(f"Results saved to: {args.output_dir}")
    print("="*60)

    return 0


if __name__ == '__main__':
    exit(main())
