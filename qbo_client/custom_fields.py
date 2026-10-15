import logging

# required for QBO to return custom fields (e.g. "Customer PO") on query results
CUSTOM_FIELDS_QUERY_PARAMS = {'include': 'enhancedAllCustomFields'}

# custom field "Type" -> key that holds its value
CUSTOM_FIELD_VALUE_KEYS = {
    'StringType': 'StringValue',
    'NumberType': 'NumberValue',
    'DateType': 'DateValue',
}

def get_custom_field(entity: dict, name: str, label: str):
    """
    Value of the custom field called `name` on a QBO entity (invoice, customer, ...), or None
    when it isn't set. `label` identifies the entity in log messages.
    """
    # QBO omits the value key when the field is blank on that entity
    for field in entity.get('CustomField', []):
        if field.get('Name') != name:
            continue

        field_type = field.get('Type')
        value_key = CUSTOM_FIELD_VALUE_KEYS.get(field_type)

        if value_key is None:
            logging.warning(f"Unsupported type '{field_type}' for custom field '{name}' on {label}")
            return None

        return field.get(value_key)
    return None
