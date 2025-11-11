"""
Cron Job Generator

Generates cron job configuration and model classes for scheduled tasks.
"""

from datetime import datetime


def generate_cron_config_xml(namespace, module, crons):
    """
    Generate config.xml crontab section for cron jobs.

    Args:
        namespace: Module namespace
        module: Module name
        crons: List of cron job definitions

    Returns:
        XML string for config.xml <crontab> section
    """
    if not crons:
        return ""

    xml = "        <crontab>\n            <jobs>\n"

    for cron in crons:
        job_name = cron.get('name')
        schedule = cron.get('schedule', '0 2 * * *')  # Default: 2 AM daily
        model = cron.get('model', f'{namespace.lower()}_{module.lower()}/observer::cron{job_name.title()}')

        xml += f"""                <{namespace.lower()}_{module.lower()}_{job_name}>
                    <schedule>
                        <cron_expr>{schedule}</cron_expr>
                    </schedule>
                    <run>
                        <model>{model}</model>
                    </run>
                </{namespace.lower()}_{module.lower()}_{job_name}>
"""

    xml += "            </jobs>\n        </crontab>\n"
    return xml


def generate_cron_model(namespace, module, crons):
    """
    Generate Model/Observer.php with cron job methods.

    Args:
        namespace: Module namespace
        module: Module name
        crons: List of cron job definitions

    Returns:
        PHP code for Model/Observer.php
    """
    if not crons:
        return None

    year = datetime.now().year
    methods = []

    for cron in crons:
        job_name = cron.get('name')
        description = cron.get('description', f'{job_name.title()} cron job')
        schedule = cron.get('schedule', '0 2 * * *')
        method_name = f"cron{job_name.title()}"

        methods.append(f"""    /**
     * {description}
     *
     * Schedule: {schedule}
     *
     * @return void
     */
    public function {method_name}()
    {{
        try {{
            // TODO: Implement {description}

            Mage::log('{namespace}_{module}: {method_name} executed successfully', Mage::LOG_INFO);
        }} catch (Exception $e) {{
            Mage::logException($e);
            Mage::log('{namespace}_{module}: {method_name} failed - ' . $e->getMessage(), Mage::LOG_ERROR);
        }}
    }}""")

    php_code = f"""<?php
/**
 * Maho
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 * @copyright  Copyright (c) {year} Maho (https://mahocommerce.com)
 * @license    https://opensource.org/licenses/OSL-3.0 Open Software License v. 3.0 (OSL-3.0)
 */

/**
 * Observer model for cron jobs
 *
 * @category   {namespace}
 * @package    {namespace}_{module}
 */
class {namespace}_{module}_Model_Observer
{{
{chr(10).join(methods)}
}}
"""

    return php_code


def get_cron_schedule_description(cron_expr):
    """
    Convert cron expression to human-readable description.

    Args:
        cron_expr: Cron expression (e.g., "0 2 * * *")

    Returns:
        Human-readable description
    """
    common_schedules = {
        '* * * * *': 'Every minute',
        '*/5 * * * *': 'Every 5 minutes',
        '*/10 * * * *': 'Every 10 minutes',
        '*/15 * * * *': 'Every 15 minutes',
        '*/30 * * * *': 'Every 30 minutes',
        '0 * * * *': 'Every hour',
        '0 */2 * * *': 'Every 2 hours',
        '0 */4 * * *': 'Every 4 hours',
        '0 0 * * *': 'Daily at midnight',
        '0 2 * * *': 'Daily at 2 AM',
        '0 0 * * 0': 'Weekly on Sunday at midnight',
        '0 0 1 * *': 'Monthly on the 1st at midnight',
    }

    return common_schedules.get(cron_expr, cron_expr)


def validate_cron_config(crons):
    """
    Validate cron job configuration.

    Args:
        crons: List of cron job definitions

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not isinstance(crons, list):
        return ["Crons must be a list"]

    seen_names = set()

    for idx, cron in enumerate(crons):
        if not isinstance(cron, dict):
            errors.append(f"Cron {idx}: Must be an object")
            continue

        # Check required fields
        if 'name' not in cron:
            errors.append(f"Cron {idx}: Missing required field 'name'")
            continue

        name = cron['name']

        # Check for duplicate names
        if name in seen_names:
            errors.append(f"Cron '{name}': Duplicate cron job name")
        seen_names.add(name)

        # Validate name format
        if not name.replace('_', '').isalnum():
            errors.append(f"Cron '{name}': Name must be alphanumeric (underscores allowed)")

        # Validate schedule if provided
        if 'schedule' in cron:
            schedule = cron['schedule']
            parts = schedule.split()
            if len(parts) != 5:
                errors.append(f"Cron '{name}': Invalid cron schedule format (must have 5 parts)")

    return errors
