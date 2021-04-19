"""

.. module:: sanitiser
   :synopsis: This is the main module of the epcis sanitiser that derives sanitised events from epcis events.
              https://github.com/european-epc-competence-center/epcis-sanitisation

.. moduleauthor:: Sebastian Schmittner <sebastian.schmittner@eecc.de>

Copyright 2021 Sebastian Schmittner

This program is free software: you can redistribute it and/or modify
it under the terms given in the LICENSE file.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the LICENSE
file for details.

"""

try:
    from .context import epcis_sanitiser
except ImportError:
    from context import epcis_sanitiser  # noqa: F401

import logging
import hashlib

from epcis_event_hash_generator import hash_generator, dl_normaliser
from epcis_sanitiser import SANITISED_FIELDS


def _hash_alg_to_fct(hashalg='sha256'):
    """
    Convert the hashalg string that specifies the hashing algorithm to be used into
    the corresponding str -> str function that produces the named identifier
    """
    if hashalg == 'sha256':
        def hash_fct(x):
            return 'ni:///sha-256;' + \
                hashlib.sha256(x.encode('utf-8')).hexdigest()
    elif hashalg == 'sha3_256':
        def hash_fct(x):
            return 'ni:///sha3_256;' + \
                hashlib.sha3_256(x.encode('utf-8')).hexdigest()
    elif hashalg == 'sha384':
        def hash_fct(x):
            return 'ni:///sha-384;' + \
                hashlib.sha384(x.encode('utf-8')).hexdigest()
    elif hashalg == 'sha512':
        def hash_fct(x):
            return 'ni:///sha-512;' + \
                hashlib.sha512(x.encode('utf-8')).hexdigest()
    else:
        raise ValueError("Unsupported Hashing Algorithm: " + hashalg)

    return hash_fct


def sanitise_events(events, dead_drop_url, hashalg='sha256', config=SANITISED_FIELDS):
    """
    Calculate the sanitized event for each event in the list and return the list of sanitized events.
    """

    logging.debug("Sanitising {}".format(events))

    hashes = hash_generator.epcis_hashes_from_events(events, hashalg)

    hash_fct = _hash_alg_to_fct(hashalg)

    sanitised_events = []
    for event, hash in zip(events[2], hashes):
        sanitised_events.append(_sanitise_event(event, hash, hash_fct, dead_drop_url, config))

    return sanitised_events


def _normalise_hash_and_salt_if_necessary(value, hash_fct, hash_salt):
    normalised = dl_normaliser.normaliser(value)
    if normalised:
        value = normalised
    if hash_salt is None:
        return value
    return hash_fct(value + hash_salt)


def _sanitise_event(event, hash, hash_fct, dead_drop_url, config):

    logging.debug("Sanitising event: %s", event)

    sanitised_event = {}

    sanitised_event["request_event_data_at"] = dead_drop_url

    for (field, hash_salt) in config.items():
        # special handling of event id (use event hash)
        if field == "eventId":
            sanitised_event[field] = _normalise_hash_and_salt_if_necessary(hash, hash_fct, hash_salt)
            continue
        # special handling of event type
        if field == "eventType":
            sanitised_event[field] = _normalise_hash_and_salt_if_necessary(event[0], hash_fct, hash_salt)
            continue

        # handling of all other keys
        for key, value, children in event[2]:
            if key == field:
                if not children:
                    sanitised_event[key] = _normalise_hash_and_salt_if_necessary(
                        value, hash_fct, hash_salt)
                else:
                    sanitised_event[key] = []
                    for (_, child_val, properties) in children:
                        sanitised_value = _normalise_hash_and_salt_if_necessary(child_val, hash_fct, hash_salt)

                        # check if the field has a type, if so add it as a query parameter
                        type_query_params = [type for (name, type, []) in properties if name == 'type']
                        if type_query_params:
                            if len(type_query_params) > 1:
                                logging.warn("More than one type parameter for %s.", child_val)
                            sanitised_value += '?type=' + "&type=".join(type_query_params)

                        sanitised_event[key].append(sanitised_value)

    return sanitised_event


def _extact_field(object, name):
    """
    Recursively search through a simple python object to find an element
    with the given name and return it.
    """
    if object[0] == name:
        return object
    for child in object[2]:
        extracted = _extact_field(child, name)
        if extracted:
            return extracted
    return None
