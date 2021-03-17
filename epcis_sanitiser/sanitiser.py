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

from epcis_event_hash_generator import hash_generator


def sanitise_events(events, hashalg='sha256'):
    """
    Calculate the sanitized event for each event in the list and return the list of sanitized events.
    """

    logging.debug("Sanitising {}".format(events))

    if hashalg == 'sha256':
        def hash_fct(x):
            return 'ni:///sha-256;' + \
                hashlib.sha256(x.encode('utf-8')).hexdigest() + '?ver=CBV2.0'
    elif hashalg == 'sha3_256':
        def hash_fct(x):
            return 'ni:///sha3_256;' + \
                hashlib.sha3_256(x.encode('utf-8')).hexdigest() + '?ver=CBV2.0'
    elif hashalg == 'sha384':
        def hash_fct(x):
            return 'ni:///sha-384;' + \
                hashlib.sha384(x.encode('utf-8')).hexdigest() + '?ver=CBV2.0'
    elif hashalg == 'sha512':
        def hash_fct(x):
            return 'ni:///sha-512;' + \
                hashlib.sha512(x.encode('utf-8')).hexdigest() + '?ver=CBV2.0'
    else:
        raise ValueError("Unsupported Hashing Algorithm: " + hashalg)

    hashes = hash_generator.epcis_hashes_from_events(events, hashalg)

    sanitised_events = []
    for event, hash in zip(events[2], hashes):
        sanitised_events.append(_sanitise_event(event, hash, hash_fct))

    return sanitised_events


def _sanitise_event(event, hash, hash_fct):

    sanitised_event = {}

    sanitised_event["eventId"] = hash

    # todo: stuff like this:
    # eventTime = _extact_field(event, "eventTime")
    # if eventTime:
    #    sanitised_event["eventTime"] = eventTime[1]

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
