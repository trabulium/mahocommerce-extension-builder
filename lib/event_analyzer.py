"""
Event Analyzer for MahoCommerce

Extracts all Mage::dispatchEvent() calls and event observers from the codebase.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional
import xml.etree.ElementTree as ET


def extract_events_from_php(file_path: Path) -> List[Dict]:
    """
    Extract all dispatchEvent calls from a PHP file.

    Returns:
        List of dicts with event info: name, file, line, context
    """
    events = []

    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        # Pattern to match Mage::dispatchEvent('event_name', ...
        pattern = r"Mage::dispatchEvent\s*\(\s*['\"]([^'\"]+)['\"]"

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                event_name = match.group(1)

                # Get some context around the event
                context_start = max(0, line_num - 3)
                context_end = min(len(lines), line_num + 2)
                context = '\n'.join(lines[context_start:context_end])

                events.append({
                    'name': event_name,
                    'file': str(file_path),
                    'line': line_num,
                    'context': context.strip(),
                    'type': 'dispatch'
                })

    except Exception as e:
        pass

    return events


def extract_observers_from_config(file_path: Path) -> List[Dict]:
    """
    Extract observer configurations from config.xml files.

    Returns:
        List of dicts with observer info: event, class, method, area
    """
    observers = []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Check different areas: global, frontend, adminhtml, admin
        for area in ['global', 'frontend', 'adminhtml', 'admin']:
            area_node = root.find(area)
            if area_node is None:
                continue

            events_node = area_node.find('events')
            if events_node is None:
                continue

            for event in events_node:
                event_name = event.tag

                observers_node = event.find('observers')
                if observers_node is None:
                    continue

                for observer in observers_node:
                    observer_name = observer.tag

                    class_node = observer.find('class')
                    method_node = observer.find('method')
                    type_node = observer.find('type')

                    observer_class = class_node.text if class_node is not None else None
                    observer_method = method_node.text if method_node is not None else None
                    observer_type = type_node.text if type_node is not None else 'singleton'

                    observers.append({
                        'event': event_name,
                        'name': observer_name,
                        'class': observer_class,
                        'method': observer_method,
                        'type': observer_type,
                        'area': area,
                        'file': str(file_path)
                    })

    except Exception as e:
        pass

    return observers


def categorize_event(event_name: str) -> str:
    """
    Categorize event by name pattern.

    Returns:
        Category name (e.g., 'customer', 'order', 'product')
    """
    event_lower = event_name.lower()

    categories = {
        'customer': ['customer', 'account', 'login', 'logout', 'register'],
        'order': ['order', 'sales_order', 'quote'],
        'product': ['product', 'catalog_product'],
        'category': ['category', 'catalog_category'],
        'cart': ['cart', 'checkout_cart'],
        'checkout': ['checkout', 'onepage'],
        'payment': ['payment', 'sales_quote_payment'],
        'shipping': ['shipping', 'shipment'],
        'invoice': ['invoice', 'sales_order_invoice'],
        'creditmemo': ['creditmemo', 'sales_order_creditmemo'],
        'newsletter': ['newsletter'],
        'cms': ['cms_page', 'cms_block', 'cms'],
        'admin': ['admin', 'adminhtml'],
        'controller': ['controller_action', 'controller_front'],
        'model': ['_save_before', '_save_after', '_save_commit_after', '_delete_before', '_delete_after', '_delete_commit_after', '_load_after'],
        'collection': ['_load_before', '_load_after'],
        'layout': ['layout', 'block_html'],
        'catalog': ['catalog'],
        'index': ['index', 'reindex'],
        'api': ['api_user'],
        'wishlist': ['wishlist'],
        'review': ['review'],
        'tag': ['tag'],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in event_lower:
                return category

    return 'other'


def analyze_events(maho_root: Path, verbose: bool = False) -> Dict:
    """
    Main event analysis function.

    Returns:
        Dict with comprehensive event information
    """
    if verbose:
        print("  Scanning for dispatchEvent() calls...")

    core_path = maho_root / 'vendor' / 'mahocommerce' / 'maho' / 'app' / 'code' / 'core' / 'Mage'
    app_core_path = maho_root / 'app' / 'code' / 'core' / 'Maho'

    all_dispatches = []
    all_observers = []

    # Scan Mage core for events
    if core_path.exists():
        for php_file in core_path.rglob('*.php'):
            events = extract_events_from_php(php_file)
            all_dispatches.extend(events)

        for config_file in core_path.rglob('config.xml'):
            observers = extract_observers_from_config(config_file)
            all_observers.extend(observers)

    # Scan Maho core for events
    if app_core_path.exists():
        for php_file in app_core_path.rglob('*.php'):
            events = extract_events_from_php(php_file)
            all_dispatches.extend(events)

        for config_file in app_core_path.rglob('config.xml'):
            observers = extract_observers_from_config(config_file)
            all_observers.extend(observers)

    if verbose:
        print(f"    Found {len(all_dispatches)} event dispatches")
        print(f"    Found {len(all_observers)} event observers")

    # Build event catalog
    event_names: Set[str] = set()
    for event in all_dispatches:
        event_names.add(event['name'])
    for observer in all_observers:
        event_names.add(observer['event'])

    # Create structured catalog
    catalog = {}
    for event_name in sorted(event_names):
        category = categorize_event(event_name)

        # Find all dispatches for this event
        dispatches = [e for e in all_dispatches if e['name'] == event_name]

        # Find all observers for this event
        observers = [o for o in all_observers if o['event'] == event_name]

        catalog[event_name] = {
            'category': category,
            'dispatched_count': len(dispatches),
            'observer_count': len(observers),
            'dispatch_locations': [
                {
                    'file': d['file'].replace(str(maho_root), ''),
                    'line': d['line']
                }
                for d in dispatches[:5]  # Limit to first 5 for size
            ],
            'observers': [
                {
                    'class': o['class'],
                    'method': o['method'],
                    'area': o['area']
                }
                for o in observers
            ]
        }

    # Group by category
    by_category = {}
    for event_name, info in catalog.items():
        category = info['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(event_name)

    # Sort events within each category
    for category in by_category:
        by_category[category].sort()

    if verbose:
        print(f"    Cataloged {len(event_names)} unique events")
        print(f"    Categories: {len(by_category)}")

    return {
        'summary': {
            'total_events': len(event_names),
            'total_dispatches': len(all_dispatches),
            'total_observers': len(all_observers),
            'categories': list(by_category.keys())
        },
        'by_category': by_category,
        'catalog': catalog,
        'common_patterns': get_common_patterns()
    }


def get_common_patterns() -> Dict:
    """
    Return common event naming patterns and when to use them.
    """
    return {
        'model_events': {
            'description': 'Model lifecycle events',
            'pattern': '{entity}_save_before, {entity}_save_after, {entity}_delete_before, etc.',
            'examples': [
                'customer_save_before',
                'customer_save_after',
                'sales_order_save_after',
                'catalog_product_delete_before'
            ],
            'use_cases': [
                'Modify data before saving',
                'Sync to external systems after save',
                'Prevent deletion with validation',
                'Clean up related data after deletion'
            ]
        },
        'controller_events': {
            'description': 'Controller action events',
            'pattern': 'controller_action_predispatch, controller_action_postdispatch',
            'examples': [
                'controller_action_predispatch',
                'controller_action_predispatch_checkout',
                'controller_action_postdispatch_customer_account_login'
            ],
            'use_cases': [
                'Add data to all pages',
                'Log user activity',
                'Modify request before processing',
                'Redirect after action'
            ]
        },
        'collection_events': {
            'description': 'Collection loading events',
            'pattern': '{collection}_load_before, {collection}_load_after',
            'examples': [
                'catalog_product_collection_load_before',
                'sales_order_collection_load_after'
            ],
            'use_cases': [
                'Add filters to collections',
                'Modify query joins',
                'Process loaded items'
            ]
        },
        'custom_events': {
            'description': 'Module-specific events you dispatch',
            'pattern': '{namespace}_{module}_{action}',
            'examples': [
                'newsletter_subscriber_save_after',
                'checkout_cart_product_add_after',
                'customer_register_success'
            ],
            'use_cases': [
                'Allow other modules to extend your functionality',
                'Trigger integrations',
                'Log custom actions'
            ]
        }
    }


def get_events_for_use_case(use_case: str, catalog: Dict) -> List[str]:
    """
    Find relevant events for a specific use case.

    Args:
        use_case: e.g., 'newsletter', 'customer', 'order'
        catalog: Event catalog from analyze_events()

    Returns:
        List of relevant event names
    """
    use_case_lower = use_case.lower()
    relevant = []

    for event_name, info in catalog['catalog'].items():
        if use_case_lower in event_name.lower():
            relevant.append(event_name)

    return sorted(relevant)
