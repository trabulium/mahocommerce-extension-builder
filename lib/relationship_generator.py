"""
Many-to-many relationship generation for MahoCommerce modules.

Copyright (c) 2025 Maho (https://mahocommerce.com)
"""


def detect_many_to_many_relationships(config, entities):
    """
    Detect many-to-many relationships from config or auto-detect from entity patterns.

    Args:
        config: Module config dict
        entities: List of entity dicts

    Returns:
        List of relationship tuples: [(entity1_name, entity2_name, relationship_name), ...]
    """
    relationships = []

    # Check if relationships are explicitly defined in config
    if 'relationships' in config:
        for rel in config['relationships']:
            if rel.get('type') == 'many_to_many':
                entity1 = rel['entity1'].lower()
                entity2 = rel['entity2'].lower()
                rel_name = f"{entity1}_{entity2}"
                relationships.append((entity1, entity2, rel_name))

    # If no explicit relationships, try auto-detection
    if not relationships:
        relationships = auto_detect_relationships(entities)

    return relationships


def auto_detect_relationships(entities):
    """
    Auto-detect many-to-many relationships based on common patterns.

    Args:
        entities: List of entity dicts

    Returns:
        List of relationship tuples: [(entity1_name, entity2_name, relationship_name), ...]
    """
    relationships = []
    entity_names = [e['name'].lower() for e in entities]

    # Common many-to-many patterns
    main_entities = ['post', 'product', 'item', 'article', 'recipe']
    related_entities = ['category', 'tag', 'cuisine', 'ingredient']

    for main in main_entities:
        if main in entity_names:
            for related in related_entities:
                if related in entity_names:
                    # Skip author as it's usually a foreign key (one-to-many), not many-to-many
                    if related not in ['author']:
                        rel_name = f"{main}_{related}"
                        relationships.append((main, related, rel_name))

    return relationships


def generate_relationship_model_methods(namespace, module, entity_name, relationships):
    """
    Generate model methods for managing many-to-many relationships.

    Args:
        namespace: Module namespace
        module: Module name
        entity_name: Current entity name
        relationships: List of relationship tuples for this entity

    Returns:
        PHP code string with relationship methods
    """
    if not relationships:
        return ""

    methods = ""

    for rel_entity1, rel_entity2, rel_name in relationships:
        # Only generate methods if this entity is part of the relationship
        if entity_name.lower() not in [rel_entity1, rel_entity2]:
            continue

        # Determine related entity name
        related_entity = rel_entity2 if entity_name.lower() == rel_entity1 else rel_entity1
        related_class = related_entity.capitalize()
        related_entities_method = f"get{related_class.rstrip('s')}s" if not related_class.endswith('s') else f"get{related_class}"

        methods += f"""
    /**
     * Get related {related_entity} IDs
     *
     * @return array
     */
    public function get{related_class}Ids()
    {{
        if (!$this->hasData('{related_entity}_ids')) {{
            $ids = [];
            foreach ($this->{related_entities_method}() as ${related_entity}) {{
                $ids[] = ${related_entity}->getId();
            }}
            $this->setData('{related_entity}_ids', $ids);
        }}
        return $this->getData('{related_entity}_ids');
    }}

    /**
     * Get related {related_entity} collection
     *
     * @return Mage_Core_Model_Resource_Db_Collection_Abstract
     */
    public function {related_entities_method}()
    {{
        if (!$this->getId()) {{
            return Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity}_collection');
        }}

        $collection = Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity}_collection');
        $collection->getSelect()->join(
            ['{rel_name}' => $collection->getTable('{namespace.lower()}_{module.lower()}/{rel_name}')],
            'main_table.{related_entity}_id = {rel_name}.{related_entity}_id AND {rel_name}.{entity_name}_id = ' . $this->getId(),
            []
        )->order('{rel_name}.position ASC');

        return $collection;
    }}
"""

    return methods


def generate_relationship_resource_methods(namespace, module, entity_name, relationships):
    """
    Generate resource model methods for saving many-to-many relationships.

    Args:
        namespace: Module namespace
        module: Module name
        entity_name: Current entity name
        relationships: List of relationship tuples for this entity

    Returns:
        PHP code string with relationship save methods
    """
    if not relationships:
        return ""

    methods = ""

    for rel_entity1, rel_entity2, rel_name in relationships:
        # Only generate methods if this entity is part of the relationship
        if entity_name.lower() not in [rel_entity1, rel_entity2]:
            continue

        # Determine related entity name
        related_entity = rel_entity2 if entity_name.lower() == rel_entity1 else rel_entity1
        related_class = related_entity.capitalize()

        methods += f"""
    /**
     * Save {related_entity} relations
     *
     * @param Mage_Core_Model_Abstract $object
     * @return $this
     */
    protected function _save{related_class}Relations(Mage_Core_Model_Abstract $object)
    {{
        $id = $object->getId();
        ${related_entity}Ids = $object->getData('{related_entity}_ids');

        if ($id && is_array(${related_entity}Ids)) {{
            $adapter = $this->_getWriteAdapter();
            $table = $this->getTable('{namespace.lower()}_{module.lower()}/{rel_name}');

            // Delete old relations
            $adapter->delete($table, ['{entity_name}_id = ?' => $id]);

            // Insert new relations
            $position = 0;
            foreach (${related_entity}Ids as ${related_entity}Id) {{
                if (!empty(${related_entity}Id)) {{
                    $adapter->insert($table, [
                        '{entity_name}_id' => $id,
                        '{related_entity}_id' => ${related_entity}Id,
                        'position' => $position++
                    ]);
                }}
            }}
        }}

        return $this;
    }}
"""

    # Add after_save hook to call relationship save methods
    if methods:
        after_save = f"""
    /**
     * Process relations after save
     *
     * @param Mage_Core_Model_Abstract $object
     * @return $this
     */
    protected function _afterSave(Mage_Core_Model_Abstract $object)
    {{
        parent::_afterSave($object);
"""

        for rel_entity1, rel_entity2, rel_name in relationships:
            if entity_name.lower() not in [rel_entity1, rel_entity2]:
                continue

            related_entity = rel_entity2 if entity_name.lower() == rel_entity1 else rel_entity1
            related_class = related_entity.capitalize()
            after_save += f"""        $this->_save{related_class}Relations($object);
"""

        after_save += """
        return $this;
    }
"""
        methods += after_save

    return methods


def generate_relationship_form_fields(namespace, module, entity_name, relationships, all_entities):
    """
    Generate form fields for many-to-many relationship management.

    Args:
        namespace: Module namespace
        module: Module name
        entity_name: Current entity name
        relationships: List of relationship tuples for this entity
        all_entities: List of all entity dicts

    Returns:
        PHP code string with multiselect fields for relationships
    """
    if not relationships:
        return ""

    form_fields = ""

    for rel_entity1, rel_entity2, rel_name in relationships:
        # Only generate fields if this entity is part of the relationship
        if entity_name.lower() not in [rel_entity1, rel_entity2]:
            continue

        # Determine related entity name
        related_entity = rel_entity2 if entity_name.lower() == rel_entity1 else rel_entity1
        related_class = related_entity.capitalize()

        # Get user-friendly label
        from .field_utils import get_field_label
        label = get_field_label({'name': related_entity + '_ids', 'label': f'{related_class}s'})

        form_fields += f"""
        $fieldset->addField('{related_entity}_ids', 'multiselect', [
            'name' => '{related_entity}_ids[]',
            'label' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('{label}'),
            'title' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('{label}'),
            'required' => false,
            'values' => Mage::getResourceModel('{namespace.lower()}_{module.lower()}/{related_entity}_collection')->toOptionArray(),
            'note' => Mage::helper('{namespace.lower()}_{module.lower()}')->__('Select {related_entity}s to associate with this {entity_name}'),
        ]);
"""

    return form_fields
