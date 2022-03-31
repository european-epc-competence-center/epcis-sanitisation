try:
    from .context import epcis_sanitiser
except ImportError:
    from context import epcis_sanitiser  # noqa: F401

from epcis_sanitiser import sanitiser

from epcis_event_hash_generator import hash_generator

import logging
import hashlib

_dead_drop_url = 'https://never.land'


def hash_fct(x):
    return 'ni:///sha-256;' + \
        hashlib.sha256(x.encode('utf-8')).hexdigest()


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

    hash_fct = sanitiser._hash_alg_to_fct()

    expected = {
        'eventType': 'ObjectEvent',
        'eventId': hash_generator.epcis_hashes_from_events(events)[0],
        'eventTime': '2020-03-04T11:00:30.000+01:00',
        'bizStep': 'urn:epcglobal:cbv:bizstep:departing',
        'action': 'OBSERVE',
        'epcList': [
            hash_fct('urn:epc:id:sscc:4012345.0000000111'),
            hash_fct('urn:epc:id:sscc:4012345.0000000222'),
            hash_fct('urn:epc:id:sscc:4012345.0000000333')
        ],
        'request_event_data_at': _dead_drop_url
    }

    sanitised = sanitiser.sanitise_events(
        events=events, dead_drop_url=_dead_drop_url)[0]

    assert expected == sanitised


def test_type_parameters():
    events = ('EventList', '',
              [
                  ('ObjectEvent', '',
                   [
                       ('bizTransactionList', '',
                        [
                            ('bizTransaction', 'urn:epc:id:gdti:0614141.00002.PO-123',
                             [
                                 ('type', 'urn:epcglobal:cbv:btt:po', [])
                             ])
                        ]),
                       ('destinationList', '',
                        [
                            ('destination', 'urn:epc:id:pgln:0614141.00000',
                             [
                                 ('type', 'urn:epcglobal:cbv:sdt:owning_party', [])
                             ])
                        ]),
                       ('sourceList', '',
                        [
                            ('source', 'urn:epc:id:pgln:4012345.00000',
                             [
                                 ('type', 'somewhere', [])
                             ])
                        ])
                   ]),
              ])

    """
    $ echo -n "urn:epc:id:pgln:0614141.00000urn:epc:id:gdti:0614141.00002.PO-123"|sha256sum 
    8d2cdc63d2e3d173174c9167ac4a857dfc0a0abba7cee54ef0e4b9a21156021b  -
    $ echo -n "urn:epc:id:pgln:4012345.00000urn:epc:id:gdti:0614141.00002.PO-123"|sha256sum 
    6fdc0ccc986c941a65c584d6181c1fbca8c29e0e9a0dc0196e83c8c4ddf96f54  -
    $ echo -n "urn:epc:id:gdti:0614141.00002.PO-123"|sha256sum 
    2428dd1fddb2811d950320b732dda8f4be7312e02be14c2dfb8da9969085da38  -
    """
    expected = {
        'eventType': 'ObjectEvent',
        'request_event_data_at': _dead_drop_url,
        'sourceList': [
            'ni:///sha-256;6fdc0ccc986c941a65c584d6181c1fbca8c29e0e9a0dc0196e83c8c4ddf96f54?type=somewhere'  # noqa: E501
        ],
        'destinationList': [
            'ni:///sha-256;8d2cdc63d2e3d173174c9167ac4a857dfc0a0abba7cee54ef0e4b9a21156021b?type=urn:epcglobal:cbv:sdt:owning_party'  # noqa: E501
        ],
        'bizTransactionList': [
            'ni:///sha-256;2428dd1fddb2811d950320b732dda8f4be7312e02be14c2dfb8da9969085da38?type=urn:epcglobal:cbv:btt:po'  # noqa: E501
        ],
        'eventId': 'ni:///sha-256;e869d45091834b775158e269ba07bed1acbc4f3fcc727a0106e34126f17b187e?ver=CBV2.0',  # noqa: E501
    }

    sanitised = sanitiser.sanitise_events(
        events=events, dead_drop_url=_dead_drop_url)[0]

    assert expected == sanitised
