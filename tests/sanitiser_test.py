try:
    from .context import epcis_sanitiser
except ImportError:
    from context import epcis_sanitiser  # noqa: F401

from epcis_sanitiser import sanitiser

from epcis_event_hash_generator import hash_generator, dl_normaliser

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
        'eventId': hash_fct(hash_generator.epcis_hashes_from_events(events)[0] + "Salt"),
        'eventTime': '2020-03-04T11:00:30.000+01:00',
        'bizStep': 'urn:epcglobal:cbv:bizstep:departing',
        'action': 'OBSERVE',
        'epcList': [
            hash_fct(dl_normaliser.normaliser('urn:epc:id:sscc:4012345.0000000111')),
            hash_fct(dl_normaliser.normaliser('urn:epc:id:sscc:4012345.0000000222')),
            hash_fct(dl_normaliser.normaliser('urn:epc:id:sscc:4012345.0000000333'))
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
                            ('bizTransaction', 'http://transaction.acme.com/po/12345678',
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

    expected = {
        'eventType': 'ObjectEvent',
        'request_event_data_at': _dead_drop_url,
        'sourceList': [
            'ni:///sha-256;4628a595d99c04a7452516059fdc4a0ffd86007dfdcd62801924472a53751098?type=somewhere'
        ],
        'destinationList': [
            'ni:///sha-256;12ec52904c050fb69dc72704f59050491caf1791353ad7ad604832ad6b0e2f26?type=urn:epcglobal:cbv:sdt:owning_party'
        ],
        'bizTransactionList': [
            'ni:///sha-256;9ec23ce8422f593d898ad0612c3332dae206fc7dd323a6359a6f3d99db635a84?type=urn:epcglobal:cbv:btt:po'
        ],
        'eventId': 'ni:///sha-256;f2599364f8cf3b8a85be9e86a71ede0881caf24ada227fc74a99f0ceaae05c64',
    }

    sanitised = sanitiser.sanitise_events(
        events=events, dead_drop_url=_dead_drop_url)[0]

    assert expected == sanitised
