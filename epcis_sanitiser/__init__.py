
"""Map of fields (as keys) to be included in the sanitised event.
The second parameter (value) is
- None if the field should be included in clear text
- a string (potentially empty) that is appended to the value befor hashing.
  Specify a non empty value for salting purposes.

If including an element with children, include all children and hash each one seperately
"""
SANITIZED_FIELDS = {
    "eventTime": None,
    "action": None,
    "parentID": "",
    "epcList": ""
}
