#!/usr/bin/env php
<?php
/**
 * Module Validation Script
 *
 * Validates that a Maho module is complete and working
 * Usage: php validate-module.php Namespace_ModuleName
 */

if ($argc < 2) {
    die("Usage: php validate-module.php Namespace_ModuleName\n");
}

$moduleName = $argv[1];
list($namespace, $module) = explode('_', $moduleName, 2);

require 'vendor/autoload.php';
Mage::app('admin');

$errors = [];
$warnings = [];

echo "Validating module: $moduleName\n";
echo str_repeat('=', 50) . "\n\n";

// 1. Check module is registered and active
echo "[1] Checking module registration...\n";
if (!Mage::getConfig()->getModuleConfig($moduleName)->is('active', 'true')) {
    $errors[] = "Module $moduleName is not active";
} else {
    echo "  ✓ Module is active\n";
}

// 2. Check helper exists
echo "\n[2] Checking helper class...\n";
$helperAlias = strtolower($namespace) . '_' . strtolower($module);
try {
    $helper = Mage::helper($helperAlias);
    if ($helper === false) {
        $errors[] = "Helper $helperAlias returns false";
    } else {
        echo "  ✓ Helper exists: " . get_class($helper) . "\n";
    }
} catch (Exception $e) {
    $errors[] = "Helper error: " . $e->getMessage();
}

// 3. Check admin controllers
echo "\n[3] Checking admin controllers...\n";
$controllerPath = "app/code/core/$namespace/$module/controllers/Adminhtml";
if (is_dir($controllerPath)) {
    $controllers = glob("$controllerPath/*Controller.php");
    foreach ($controllers as $file) {
        $className = "{$namespace}_{$module}_Adminhtml_" . basename($file, '.php');
        if (class_exists($className)) {
            echo "  ✓ Controller exists: $className\n";

            // Check if controller can be instantiated
            try {
                $controller = new $className(
                    new Mage_Core_Controller_Request_Http(),
                    new Mage_Core_Controller_Response_Http()
                );
                echo "    ✓ Can instantiate\n";
            } catch (Exception $e) {
                $warnings[] = "Controller $className instantiation warning: " . $e->getMessage();
            }
        } else {
            $errors[] = "Controller class $className not found (file exists but class doesn't)";
        }
    }
} else {
    $warnings[] = "No admin controllers directory found";
}

// 4. Check blocks
echo "\n[4] Checking blocks...\n";
$blockPath = "app/code/core/$namespace/$module/Block";
if (is_dir($blockPath)) {
    $blockAlias = strtolower($namespace) . '_' . strtolower($module);

    // Find all block files
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($blockPath)
    );

    foreach ($iterator as $file) {
        if ($file->isFile() && $file->getExtension() === 'php') {
            $relativePath = substr($file->getPathname(), strlen($blockPath) + 1, -4);
            $blockName = str_replace('/', '_', strtolower($relativePath));
            $fullAlias = $blockAlias . '/' . $blockName;

            try {
                $block = Mage::app()->getLayout()->createBlock($fullAlias);
                if ($block === false) {
                    $errors[] = "Block $fullAlias returns false";
                } else {
                    echo "  ✓ Block works: $fullAlias -> " . get_class($block) . "\n";
                }
            } catch (Exception $e) {
                $errors[] = "Block $fullAlias error: " . $e->getMessage();
            }
        }
    }
}

// 5. Check layout XML files
echo "\n[5] Checking layout XML...\n";
$layoutPath = "app/design/adminhtml/default/default/layout/" . strtolower($namespace) . "/" . strtolower($module) . ".xml";
if (file_exists($layoutPath)) {
    echo "  ✓ Layout file exists: $layoutPath\n";

    // Parse and validate XML
    $xml = simplexml_load_file($layoutPath);
    if ($xml === false) {
        $errors[] = "Layout XML is invalid";
    } else {
        $handles = [];
        foreach ($xml->children() as $handle) {
            $handles[] = $handle->getName();
        }
        echo "    Found " . count($handles) . " layout handles\n";
        foreach ($handles as $handle) {
            echo "      - $handle\n";
        }
    }
} else {
    $warnings[] = "No adminhtml layout XML found at $layoutPath";
}

// 6. Check models
echo "\n[6] Checking models...\n";
$modelPath = "app/code/core/$namespace/$module/Model";
if (is_dir($modelPath)) {
    $modelAlias = strtolower($namespace) . '_' . strtolower($module);

    // Find model files (not Resource)
    $files = glob("$modelPath/*.php");
    foreach ($files as $file) {
        $modelName = strtolower(basename($file, '.php'));
        $fullAlias = $modelAlias . '/' . $modelName;

        try {
            $model = Mage::getModel($fullAlias);
            if ($model === false) {
                $errors[] = "Model $fullAlias returns false";
            } else {
                echo "  ✓ Model works: $fullAlias -> " . get_class($model) . "\n";
            }
        } catch (Exception $e) {
            $errors[] = "Model $fullAlias error: " . $e->getMessage();
        }
    }
}

// 7. Check routing
echo "\n[7] Checking admin routing...\n";
$config = Mage::getConfig();
$adminRouters = $config->getNode('admin/routers/adminhtml/args/modules');
if ($adminRouters) {
    foreach ($adminRouters->children() as $name => $module) {
        if (strpos((string)$module, $namespace . '_' . $module) !== false) {
            echo "  ✓ Admin route registered: $name -> $module\n";
        }
    }
}

// Summary
echo "\n" . str_repeat('=', 50) . "\n";
echo "VALIDATION SUMMARY\n";
echo str_repeat('=', 50) . "\n";

if (count($errors) > 0) {
    echo "\n❌ ERRORS (" . count($errors) . "):\n";
    foreach ($errors as $error) {
        echo "  - $error\n";
    }
}

if (count($warnings) > 0) {
    echo "\n⚠️  WARNINGS (" . count($warnings) . "):\n";
    foreach ($warnings as $warning) {
        echo "  - $warning\n";
    }
}

if (count($errors) === 0) {
    echo "\n✅ Module validation PASSED\n";
    exit(0);
} else {
    echo "\n❌ Module validation FAILED\n";
    exit(1);
}
