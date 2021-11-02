
"""Map of fields (as keys) to be included in the sanitised event.
The second parameter (value) is
- None if the field should be included in clear text
- a string (potentially empty) that is appended to the value befor hashing.
  Specify a non empty value for salting purposes.

If including an element with children, include all children and hash each one separately.

This is the default used. Run the cli tool with '-c some_config.json' to load other values,
 in particular in order to set salts.
"""
DEFAULT_CONFIG = {
    "dead_drop_url": "",
    "sanitised_fields": {
        "eventType": None,
        "eventId": "Salt",
        "eventTime": None,
        "action": None,
        "parentID": "Salt",
        "epcList": "",
        "inputEPCList": "",
        "outputEPCList": "",
        "childEPCs": "",
        "quantityList": "",
        "childQuantityList": "",
        "inputQuantityList": "",
        "outputQuantityList": "",
        "bizStep": None,
        "sourceList": "source",
        "destinationList": "destination",
        "bizTransactionList": ""
    }
}
