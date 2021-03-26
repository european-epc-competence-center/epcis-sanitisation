try:
    from .context import epcis_sanitiser
except ImportError:
    from context import epcis_sanitiser  # noqa: F401

from epcis_sanitiser import sanitiser

from epcis_event_hash_generator import hash_generator

import logging
import hashlib


def hash_fct(x):
    return 'ni:///sha-256;' + \
        hashlib.sha256(x.encode('utf-8')).hexdigest() + '?ver=CBV2.0'


def test_sanitisation(caplog):
    caplog.set_level(logging.DEBUG)

    events = ('EventList', '', [
        ('ObjectEvent', '', [
            ('action', 'OBSERVE', []),
            ('bizStep', 'urn:epcglobal:cbv:bizstep:departing', []),
            ('epcList', '', [
                ('epc', 'urn:epc:id:sscc:4012345.0000000111', []),
                ('epc', 'urn:epc:id:sscc:4012345.0000000222', []),
                ('epc', 'urn:epc:id:sscc:4012345.0000000333', [])
            ]),
            ('eventTime', '2020-03-04T11:00:30.000+01:00', []),
            ('eventTimeZoneOffset', '+01:00', []),
            ('readPoint', '', [
                          ('id', 'urn:epc:id:sgln:4012345.00011.987', [])
            ]),
            ('recordTime', '2020-03-04T11:00:30.999+01:00', []),
        ])
    ])

    hash_fct = sanitiser.hash_alg_to_fct()

    expected = {
        'eventId': hash_fct(hash_generator.epcis_hashes_from_events(events)[0] + "Salt"),
        'eventTime': '2020-03-04T11:00:30.000+01:00',
        'bizStep': 'urn:epcglobal:cbv:bizstep:departing',
        'action': 'OBSERVE',
        'epcList': [
            hash_fct('urn:epc:id:sscc:4012345.0000000111'),
            hash_fct('urn:epc:id:sscc:4012345.0000000222'),
            hash_fct('urn:epc:id:sscc:4012345.0000000333')
        ],
        'request_event_data_at': 'https://never.land'
    }

    sanitised = sanitiser.sanitise_events(
        events=events, dead_drop_url='https://never.land')[0]

    assert expected == sanitised
