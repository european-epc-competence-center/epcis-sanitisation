# EPCIS Sanitisation Prototype

[![Build Status](https://github.com/european-epc-competence-center/epcis-sanitisation/workflows/Unit%20Tests/badge.svg?v=42)](https://github.com/RalphTro/epcis-event-hash-generator/actions?query=workflow%3A%22Unit+Tests%22)
[![Linter Status](https://github.com/european-epc-competence-center/epcis-sanitisation/workflows/Code%20Style/badge.svg)](https://github.com/RalphTro/epcis-event-hash-generator/actions?query=workflow%3A%22Code+Style%22)

As part of a collaborative approach to solve the discovery problem and related read rights management of distributed EPCIS repositories, this repository hosts conceptual documents and prototypical implementations of tools to hide (sanitise) EPCIS event data.

The EPCIS document parsing and hashing functionality of this project is imported from https://github.com/RalphTro/epcis-event-hash-generator. See there for details.

## Background

Supply chain traceability systems have become central in many industries, such as electronics, apparel, food and pharmaceuticals. However, traceability data is often highly commercial sensitive, and firms seek to keep it confidential to protect their competitive advantage. This is at odds with calls for greater transparency that would, for example, enable product passports to enhance reusability and recyclability of products or data-based product specific CO2 footprint calculations. Therefore, a solution to this conflict of interest known as the discovery problem is needed. 

This software prototype provides a vital building block to accomplish this goal in sanitising such sensitive traceability data (formatted as EPCIS events) through hashing contained business object/party identifiers as well as stripping off dispensable data. Thereby, it enables interested parties to investigate and demonstrate that sanitised data can be used to confirm the authenticity of products and provide a basis for anonymously verifying the rights of an actor to access detailed traceability data. 

## CLI Usage

Run the CLI like
```
epcis_sanitiser/__main__.py tests/events/ReferenceEventHashAlgorithm.xml
```
Run with `-h` for usage information.

## Web Service Usage

Start the web service like
```
epcis_sanitiser/webservice.py -p 8000
```
Run with `-h` for usage information.

Instances of those webservices for demo/testing purposes are running at

- https://discovery.epcat.de/docs
- https://discovery.epcat.de/dead_drop/docs

Note that these demo services may wipe there database or be unavaiable any time. Do not use beyond ad hoc testing.

### Example XML: POST
```
curl -X 'POST' \
  'http://127.0.0.1:8000/sanitise_xml_event/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "xml_epcis_document": "<?xml version=\"1.0\" ?> <epcis:EPCISDocument xmlns:epcis=\"urn:epcglobal:epcis:xsd:1\"   xmlns:https=\"https://ns.example.com/epcis\"    xmlns:example=\"https://ns.example.com/epcis\" schemaVersion=\"1.2\" creationDate=\"2020-03-03T13:07:51.709Z\">    <EPCISBody>        <EventList>            <ObjectEvent>                <eventTime>2020-03-04T11:00:30.000+01:00</eventTime>                <recordTime>2020-03-04T11:00:30.999+01:00</recordTime>                <eventTimeZoneOffset>+01:00</eventTimeZoneOffset>                <epcList>                    <epc>urn:epc:id:sscc:4012345.0000000333</epc>                    <epc>urn:epc:id:sscc:4012345.0000000111</epc>                    <epc>urn:epc:id:sscc:4012345.0000000222</epc>                </epcList>                <action>OBSERVE</action>                <bizStep>urn:epcglobal:cbv:bizstep:departing</bizStep>                <readPoint>                    <id>urn:epc:id:sgln:4012345.00011.987</id>                </readPoint>                <example:myField1>                    <example:mySubField1>2</example:mySubField1>                    <example:mySubField2>5</example:mySubField2>                </example:myField1>                <https:myField2>0</https:myField2>                <https:myField3>                    <example:mySubField3>3</example:mySubField3>                    <example:mySubField3>1</example:mySubField3>                </https:myField3>            </ObjectEvent>        </EventList>    </EPCISBody></epcis:EPCISDocument>"
}'
```

### Example: JSON POST
```
curl -X 'POST' \
  'http://127.0.0.1:8000/sanitise_json_event/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "@context": "https://id.gs1.org/epcis-context.jsonld",
  "isA": "EPCISDocument",
  "creationDate": "2020-03-03T13:07:51.709+00:00",
  "schemaVersion": 1.2,
  "format": "application/ld+json",
  "epcisBody": {
    "eventList": [
      {
        "isA": "ObjectEvent",
        "eventTime": "2020-03-04T11:00:30.000+01:00",
        "eventTimeZoneOffset": "+01:00",
        "recordTime": "2020-03-04T11:00:30.999+01:00",
        "epcList": [
          "urn:epc:id:sscc:4012345.0000000333",
          "urn:epc:id:sscc:4012345.0000000111",
          "urn:epc:id:sscc:4012345.0000000222"
        ],
        "action": "OBSERVE",
        "bizStep": "urn:epcglobal:cbv:bizstep:departing",
        "readPoint": {"id": "urn:epc:id:sgln:4012345.00011.987"},
        "example:myField1": {
          "@xmlns:example": "https://ns.example.com/epcis",
          "example:mySubField1": "2",
          "example:mySubField2": "5"
        },
        "example:myField2": {
          "@xmlns:example": "https://ns.example.com/epcis",
          "#text": "0"
        },
        "example:myField3": {
          "@xmlns:example": "https://ns.example.com/epcis",
          "example:mySubField3": [
            "3",
            "1"
          ]
        }
      }
    ]
  }
}'
```

### Example: EPC query

```
http://127.0.0.1:8000/events_for_epc/sha-256%3B1ac005312f9635d448b8ccb7a45f8bba8cccd257025aa06cd1f6445f79cb957c
```

### Example: Event ID query
```
http://127.0.0.1:8000/event/sha-256%3B8b089483649d983ea03cfc8d6743beba644eb1cfb5bfc654ec8484a98263c901
```

## License

Copyright (c) 2020-2021 GS1 Germany, European EPC Competence Center GmbH (EECC)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
