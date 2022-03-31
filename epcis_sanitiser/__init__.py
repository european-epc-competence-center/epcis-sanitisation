
"""Map of fields (as keys) to be included in the sanitised event.
The second parameter (value) is
- None if the field should be included in clear text
- a string (potentially empty) that is appended to the value befor hashing.
  Specify a non empty value for salting purposes.

If including an element with children, all children are hashed separately.

This is the default used. Run the cli tool with '-c some_config.json' to load other values,
 in particular in order to set salts.
"""
DEFAULT_CONFIG = {
    "dead_drop_url": "",
    "sanitised_fields": {
        "eventType": None,
        "eventId": None,
        "eventTime": None,
        "action": None,
        "parentID": None,
        "epcList": "",
        "inputEPCList": "",
        "outputEPCList": "",
        "childEPCs": "",
        "quantityList": "",
        "childQuantityList": "",
        "inputQuantityList": "",
        "outputQuantityList": "",
        "bizStep": None,
        "sourceList": "urn:epc:id:gdti:0614141.00002.PO-123",
        "destinationList": "urn:epc:id:gdti:0614141.00002.PO-123",
        "bizTransactionList": ""
    }
}
