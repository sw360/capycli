# -------------------------------------------------------------------------------
# Copyright (c) 2024 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

from cyclonedx.model import LicenseChoice, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component

from capycli.common.capycli_bom_support import SbomJsonParser
from tests.test_base import TestBase


class TestSbomLicenseVariants(TestBase):
    def test_license_expression(self) -> None:
        SBOM = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.3",
            "version": 1,
            "serialNumber": "urn:uuid:102596b3-881c-44f1-b12e-19ea42ab73e8",
            "metadata": {
                "timestamp": "2024-10-04T08:00:00.693380684Z",
                "tools": [
                    {
                        "vendor": "CycloneDX",
                        "name": "cargo-cyclonedx",
                        "version": "0.5.0"
                    }
                ],
            },
            "components": [
                {
                    "type": "library",
                    "bom-ref": "registry+https://github.com/rust-lang/crates.io-index#unicode-ident@1.0.13",
                    "name": "unicode-ident",
                    "version": "1.0.13",
                    "description": "Determine whether characters have...",
                    "scope": "required",
                    "hashes": [
                        {
                            "alg": "SHA-256",
                            "content": "e91b56cd4cadaeb79bbf1a5645f6b4f8dc5bde8834ad5894a8db35fda9efa1fe"
                        }
                    ],
                    "licenses": [
                        {
                            "expression": "(MIT OR Apache-2.0) AND Unicode-DFS-2016"
                        }
                    ],
                    "purl": "pkg:cargo/unicode-ident@1.0.13",
                    "externalReferences": [
                        {
                            "type": "documentation",
                            "url": "https://docs.rs/unicode-ident"
                        },
                        {
                            "type": "vcs",
                            "url": "https://github.com/dtolnay/unicode-ident"
                        }
                    ]
                }
            ]
        }

        parser = SbomJsonParser(SBOM)
        bom = Bom.from_parser(parser=parser)

        self.assertIsNotNone(bom)
        self.assertIsNotNone(bom.metadata)
        self.assertIsNotNone(bom.components)
        self.assertEqual(1, len(bom.components))
        comp: Component = bom.components[0]
        self.assertEqual("unicode-ident", comp.name)
        self.assertEqual("1.0.13", comp.version)
        self.assertEqual(1, len(comp.hashes))
        self.assertEqual(1, len(comp.licenses))
        lchoice: LicenseChoice = comp.licenses[0]
        self.assertIsNone(lchoice.license)
        self.assertIsNotNone(lchoice.expression)
        self.assertEqual("(MIT OR Apache-2.0) AND Unicode-DFS-2016", lchoice.expression)

    def test_license_id(self) -> None:
        SBOM = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.3",
            "version": 1,
            "serialNumber": "urn:uuid:102596b3-881c-44f1-b12e-19ea42ab73e8",
            "metadata": {
                "timestamp": "2024-10-04T08:00:00.693380684Z",
                "tools": [
                    {
                        "vendor": "CycloneDX",
                        "name": "cargo-cyclonedx",
                        "version": "0.5.0"
                    }
                ],
            },
            "components": [
                {
                    "type": "library",
                    "bom-ref": "registry+https://github.com/rust-lang/crates.io-index#ring@0.17.8",
                    "name": "ring",
                    "version": "0.17.8",
                    "description": "Safe, fast, small crypto using Rust.",
                    "scope": "required",
                    "hashes": [
                        {
                            "alg": "SHA-256",
                            "content": "c17fa4cb658e3583423e915b9f3acc01cceaee1860e33d59ebae66adc3a2dc0d"
                        }
                    ],
                    "licenses": [
                        {
                            "license": {
                                "id": "Apache-2.0",
                                "name": "Apache Software License, 2.0",
                                "url": "https://www.apache.org/licenses/LICENSE-2.0.txt"
                            }
                        }
                    ],
                    "purl": "pkg:cargo/ring@0.17.8",
                    "externalReferences": [
                        {
                            "type": "other",
                            "url": "ring_core_0_17_8"
                        },
                        {
                            "type": "vcs",
                            "url": "https://github.com/briansmith/ring"
                        }
                    ]
                }
            ]
        }

        parser = SbomJsonParser(SBOM)
        bom = Bom.from_parser(parser=parser)
        bom.metadata.tools = parser.get_tools()
        bom.metadata.licenses = parser.get_metadata_licenses()
        bom.metadata.properties = parser.get_metadata_properties()

        self.assertIsNotNone(bom)
        self.assertIsNotNone(bom.metadata)
        self.assertIsNotNone(bom.components)
        self.assertEqual(1, len(bom.components))
        comp: Component = bom.components[0]
        self.assertEqual("ring", comp.name)
        self.assertEqual("0.17.8", comp.version)
        self.assertEqual(1, len(comp.hashes))
        self.assertEqual(1, len(comp.licenses))
        lchoice: LicenseChoice = comp.licenses[0]
        self.assertIsNotNone(lchoice.license)
        self.assertIsNone(lchoice.expression)
        if lchoice.license:  # only because of mypy
            self.assertIsNotNone(lchoice.license.id)
            self.assertEqual("Apache-2.0", lchoice.license.id)
            self.assertTrue(isinstance(lchoice.license.url, XsUri))
            self.assertEqual("https://www.apache.org/licenses/LICENSE-2.0.txt", str(lchoice.license.url))
            # NOTE: CycloneDX spec 1.4:
            # "If SPDX does not define the license used, this field may be used to provide the license name"
            # The CycloneDX python lib just ignores the name if id (=SPDX) has been specified!
            # NOT: self.assertEqual("Apache Software License, 2.0", lchoice.license.name)
            # BUT:
            self.assertIsNone(lchoice.expression)

    def test_license_name(self) -> None:
        SBOM = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.3",
            "version": 1,
            "serialNumber": "urn:uuid:102596b3-881c-44f1-b12e-19ea42ab73e8",
            "metadata": {
                "timestamp": "2024-10-04T08:00:00.693380684Z",
                "tools": [
                    {
                        "vendor": "CycloneDX",
                        "name": "cargo-cyclonedx",
                        "version": "0.5.0"
                    }
                ],
            },
            "components": [
                {
                    "type": "library",
                    "bom-ref": "registry+https://github.com/rust-lang/crates.io-index#ring@0.17.8",
                    "name": "ring",
                    "version": "0.17.8",
                    "description": "Safe, fast, small crypto using Rust.",
                    "scope": "required",
                    "hashes": [
                        {
                            "alg": "SHA-256",
                            "content": "c17fa4cb658e3583423e915b9f3acc01cceaee1860e33d59ebae66adc3a2dc0d"
                        }
                    ],
                    "licenses": [
                        {
                            "license": {
                                "name": "Apache Software License, 2.0",
                                "url": "https://www.apache.org/licenses/LICENSE-2.0.txt"
                            }
                        }
                    ],
                    "purl": "pkg:cargo/ring@0.17.8",
                    "externalReferences": [
                        {
                            "type": "other",
                            "url": "ring_core_0_17_8"
                        },
                        {
                            "type": "vcs",
                            "url": "https://github.com/briansmith/ring"
                        }
                    ]
                }
            ]
        }

        parser = SbomJsonParser(SBOM)
        bom = Bom.from_parser(parser=parser)

        self.assertIsNotNone(bom)
        self.assertIsNotNone(bom.metadata)
        self.assertIsNotNone(bom.components)
        self.assertEqual(1, len(bom.components))
        comp: Component = bom.components[0]
        self.assertEqual("ring", comp.name)
        self.assertEqual("0.17.8", comp.version)
        self.assertEqual(1, len(comp.hashes))
        self.assertEqual(1, len(comp.licenses))
        lchoice: LicenseChoice = comp.licenses[0]
        self.assertIsNotNone(lchoice.license)
        self.assertIsNone(lchoice.expression)
        if lchoice.license:  # only because of mypy
            self.assertIsNotNone(lchoice.license.name)
            self.assertEqual("Apache Software License, 2.0", lchoice.license.name)
            self.assertIsNone(lchoice.license.id)
            self.assertTrue(isinstance(lchoice.license.url, XsUri))
            self.assertEqual("https://www.apache.org/licenses/LICENSE-2.0.txt", str(lchoice.license.url))
        self.assertIsNone(lchoice.expression)

    def test_license_text(self) -> None:
        SBOM = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.3",
            "version": 1,
            "serialNumber": "urn:uuid:102596b3-881c-44f1-b12e-19ea42ab73e8",
            "metadata": {
                "timestamp": "2024-10-04T08:00:00.693380684Z",
                "tools": [
                    {
                        "vendor": "CycloneDX",
                        "name": "cargo-cyclonedx",
                        "version": "0.5.0"
                    }
                ],
            },
            "components": [
                {
                    "type": "library",
                    "bom-ref": "registry+https://github.com/rust-lang/crates.io-index#ring@0.17.8",
                    "name": "ring",
                    "version": "0.17.8",
                    "description": "Safe, fast, small crypto using Rust.",
                    "scope": "required",
                    "hashes": [
                        {
                            "alg": "SHA-256",
                            "content": "c17fa4cb658e3583423e915b9f3acc01cceaee1860e33d59ebae66adc3a2dc0d"
                        }
                    ],
                    "licenses": [
                        {
                            "license": {
                                "name": "Unknown",
                                "text": {
                                    "encoding": "base64",
                                    "content": "Tm90ZSB0aGF0IGl0IGlzIGVhc3kgZm9yIHRoaXMgZmlsZSB0byBnZXQgb3V0IG9mIHN5bmMgd2l0aCB0aGUgbGljZW5zZXMgaW4gdGhlCnNvdXJjZSBjb2RlIGZpbGVzLiBJdCdzIHJlY29tbWVuZGVkIHRvIGNvbXBhcmUgdGhlIGxpY2Vuc2VzIGluIHRoZSBzb3VyY2UgY29kZQp3aXRoIHdoYXQncyBtZW50aW9uZWQgaGVyZS4KCipyaW5nKiBpcyBkZXJpdmVkIGZyb20gQm9yaW5nU1NMLCBzbyB0aGUgbGljZW5zaW5nIHNpdHVhdGlvbiBpbiAqcmluZyogaXMKc2ltaWxhciB0byBCb3JpbmdTU0wuCgoqcmluZyogdXNlcyBhbiBJU0Mtc3R5bGUgbGljZW5zZSBsaWtlIEJvcmluZ1NTTCBmb3IgY29kZSBpbiBuZXcgZmlsZXMsCmluY2x1ZGluZyBpbiBwYXJ0aWN1bGFyIGFsbCB0aGUgUnVzdCBjb2RlOgoKICAgQ29weXJpZ2h0IDIwMTUtMjAxNiBCcmlhbiBTbWl0aC4KCiAgIFBlcm1pc3Npb24gdG8gdXNlLCBjb3B5LCBtb2RpZnksIGFuZC9vciBkaXN0cmlidXRlIHRoaXMgc29mdHdhcmUgZm9yIGFueQogICBwdXJwb3NlIHdpdGggb3Igd2l0aG91dCBmZWUgaXMgaGVyZWJ5IGdyYW50ZWQsIHByb3ZpZGVkIHRoYXQgdGhlIGFib3ZlCiAgIGNvcHlyaWdodCBub3RpY2UgYW5kIHRoaXMgcGVybWlzc2lvbiBub3RpY2UgYXBwZWFyIGluIGFsbCBjb3BpZXMuCgogICBUSEUgU09GVFdBUkUgSVMgUFJPVklERUQgIkFTIElTIiBBTkQgVEhFIEFVVEhPUlMgRElTQ0xBSU0gQUxMIFdBUlJBTlRJRVMKICAgV0lUSCBSRUdBUkQgVE8gVEhJUyBTT0ZUV0FSRSBJTkNMVURJTkcgQUxMIElNUExJRUQgV0FSUkFOVElFUyBPRgogICBNRVJDSEFOVEFCSUxJVFkgQU5EIEZJVE5FU1MuIElOIE5PIEVWRU5UIFNIQUxMIFRIRSBBVVRIT1JTIEJFIExJQUJMRSBGT1IgQU5ZCiAgIFNQRUNJQUwsIERJUkVDVCwgSU5ESVJFQ1QsIE9SIENPTlNFUVVFTlRJQUwgREFNQUdFUyBPUiBBTlkgREFNQUdFUwogICBXSEFUU09FVkVSIFJFU1VMVElORyBGUk9NIExPU1MgT0YgVVNFLCBEQVRBIE9SIFBST0ZJVFMsIFdIRVRIRVIgSU4gQU4gQUNUSU9OCiAgIE9GIENPTlRSQUNULCBORUdMSUdFTkNFIE9SIE9USEVSIFRPUlRJT1VTIEFDVElPTiwgQVJJU0lORyBPVVQgT0YgT1IgSU4KICAgQ09OTkVDVElPTiBXSVRIIFRIRSBVU0UgT1IgUEVSRk9STUFOQ0UgT0YgVEhJUyBTT0ZUV0FSRS4KCkJvcmluZ1NTTCBpcyBhIGZvcmsgb2YgT3BlblNTTC4gQXMgc3VjaCwgbGFyZ2UgcGFydHMgb2YgaXQgZmFsbCB1bmRlciBPcGVuU1NMCmxpY2Vuc2luZy4gRmlsZXMgdGhhdCBhcmUgY29tcGxldGVseSBuZXcgaGF2ZSBhIEdvb2dsZSBjb3B5cmlnaHQgYW5kIGFuIElTQwpsaWNlbnNlLiBUaGlzIGxpY2Vuc2UgaXMgcmVwcm9kdWNlZCBhdCB0aGUgYm90dG9tIG9mIHRoaXMgZmlsZS4KCkNvbnRyaWJ1dG9ycyB0byBCb3JpbmdTU0wgYXJlIHJlcXVpcmVkIHRvIGZvbGxvdyB0aGUgQ0xBIHJ1bGVzIGZvciBDaHJvbWl1bToKaHR0cHM6Ly9jbGEuZGV2ZWxvcGVycy5nb29nbGUuY29tL2NsYXMKCkZpbGVzIGluIHRoaXJkX3BhcnR5LyBoYXZlIHRoZWlyIG93biBsaWNlbnNlcywgYXMgZGVzY3JpYmVkIHRoZXJlaW4uIFRoZSBNSVQKbGljZW5zZSwgZm9yIHRoaXJkX3BhcnR5L2ZpYXQsIHdoaWNoLCB1bmxpa2Ugb3RoZXIgdGhpcmRfcGFydHkgZGlyZWN0b3JpZXMsIGlzCmNvbXBpbGVkIGludG8gbm9uLXRlc3QgbGlicmFyaWVzLCBpcyBpbmNsdWRlZCBiZWxvdy4KClRoZSBPcGVuU1NMIHRvb2xraXQgc3RheXMgdW5kZXIgYSBkdWFsIGxpY2Vuc2UsIGkuZS4gYm90aCB0aGUgY29uZGl0aW9ucyBvZiB0aGUKT3BlblNTTCBMaWNlbnNlIGFuZCB0aGUgb3JpZ2luYWwgU1NMZWF5IGxpY2Vuc2UgYXBwbHkgdG8gdGhlIHRvb2xraXQuIFNlZSBiZWxvdwpmb3IgdGhlIGFjdHVhbCBsaWNlbnNlIHRleHRzLiBBY3R1YWxseSBib3RoIGxpY2Vuc2VzIGFyZSBCU0Qtc3R5bGUgT3BlbiBTb3VyY2UKbGljZW5zZXMuIEluIGNhc2Ugb2YgYW55IGxpY2Vuc2UgaXNzdWVzIHJlbGF0ZWQgdG8gT3BlblNTTCBwbGVhc2UgY29udGFjdApvcGVuc3NsLWNvcmVAb3BlbnNzbC5vcmcuCgpUaGUgZm9sbG93aW5nIGFyZSBHb29nbGUtaW50ZXJuYWwgYnVnIG51bWJlcnMgd2hlcmUgZXhwbGljaXQgcGVybWlzc2lvbiBmcm9tCnNvbWUgYXV0aG9ycyBpcyByZWNvcmRlZCBmb3IgdXNlIG9mIHRoZWlyIHdvcms6CiAgMjcyODcxOTkKICAyNzI4Nzg4MAogIDI3Mjg3ODgzCgogIE9wZW5TU0wgTGljZW5zZQogIC0tLS0tLS0tLS0tLS0tLQoKLyogPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0KICogQ29weXJpZ2h0IChjKSAxOTk4LTIwMTEgVGhlIE9wZW5TU0wgUHJvamVjdC4gIEFsbCByaWdodHMgcmVzZXJ2ZWQuCiAqCiAqIFJlZGlzdHJpYnV0aW9uIGFuZCB1c2UgaW4gc291cmNlIGFuZCBiaW5hcnkgZm9ybXMsIHdpdGggb3Igd2l0aG91dAogKiBtb2RpZmljYXRpb24sIGFyZSBwZXJtaXR0ZWQgcHJvdmlkZWQgdGhhdCB0aGUgZm9sbG93aW5nIGNvbmRpdGlvbnMKICogYXJlIG1ldDoKICoKICogMS4gUmVkaXN0cmlidXRpb25zIG9mIHNvdXJjZSBjb2RlIG11c3QgcmV0YWluIHRoZSBhYm92ZSBjb3B5cmlnaHQKICogICAgbm90aWNlLCB0aGlzIGxpc3Qgb2YgY29uZGl0aW9ucyBhbmQgdGhlIGZvbGxvd2luZyBkaXNjbGFpbWVyLiAKICoKICogMi4gUmVkaXN0cmlidXRpb25zIGluIGJpbmFyeSBmb3JtIG11c3QgcmVwcm9kdWNlIHRoZSBhYm92ZSBjb3B5cmlnaHQKICogICAgbm90aWNlLCB0aGlzIGxpc3Qgb2YgY29uZGl0aW9ucyBhbmQgdGhlIGZvbGxvd2luZyBkaXNjbGFpbWVyIGluCiAqICAgIHRoZSBkb2N1bWVudGF0aW9uIGFuZC9vciBvdGhlciBtYXRlcmlhbHMgcHJvdmlkZWQgd2l0aCB0aGUKICogICAgZGlzdHJpYnV0aW9uLgogKgogKiAzLiBBbGwgYWR2ZXJ0aXNpbmcgbWF0ZXJpYWxzIG1lbnRpb25pbmcgZmVhdHVyZXMgb3IgdXNlIG9mIHRoaXMKICogICAgc29mdHdhcmUgbXVzdCBkaXNwbGF5IHRoZSBmb2xsb3dpbmcgYWNrbm93bGVkZ21lbnQ6CiAqICAgICJUaGlzIHByb2R1Y3QgaW5jbHVkZXMgc29mdHdhcmUgZGV2ZWxvcGVkIGJ5IHRoZSBPcGVuU1NMIFByb2plY3QKICogICAgZm9yIHVzZSBpbiB0aGUgT3BlblNTTCBUb29sa2l0LiAoaHR0cDovL3d3dy5vcGVuc3NsLm9yZy8pIgogKgogKiA0LiBUaGUgbmFtZXMgIk9wZW5TU0wgVG9vbGtpdCIgYW5kICJPcGVuU1NMIFByb2plY3QiIG11c3Qgbm90IGJlIHVzZWQgdG8KICogICAgZW5kb3JzZSBvciBwcm9tb3RlIHByb2R1Y3RzIGRlcml2ZWQgZnJvbSB0aGlzIHNvZnR3YXJlIHdpdGhvdXQKICogICAgcHJpb3Igd3JpdHRlbiBwZXJtaXNzaW9uLiBGb3Igd3JpdHRlbiBwZXJtaXNzaW9uLCBwbGVhc2UgY29udGFjdAogKiAgICBvcGVuc3NsLWNvcmVAb3BlbnNzbC5vcmcuCiAqCiAqIDUuIFByb2R1Y3RzIGRlcml2ZWQgZnJvbSB0aGlzIHNvZnR3YXJlIG1heSBub3QgYmUgY2FsbGVkICJPcGVuU1NMIgogKiAgICBub3IgbWF5ICJPcGVuU1NMIiBhcHBlYXIgaW4gdGhlaXIgbmFtZXMgd2l0aG91dCBwcmlvciB3cml0dGVuCiAqICAgIHBlcm1pc3Npb24gb2YgdGhlIE9wZW5TU0wgUHJvamVjdC4KICoKICogNi4gUmVkaXN0cmlidXRpb25zIG9mIGFueSBmb3JtIHdoYXRzb2V2ZXIgbXVzdCByZXRhaW4gdGhlIGZvbGxvd2luZwogKiAgICBhY2tub3dsZWRnbWVudDoKICogICAgIlRoaXMgcHJvZHVjdCBpbmNsdWRlcyBzb2Z0d2FyZSBkZXZlbG9wZWQgYnkgdGhlIE9wZW5TU0wgUHJvamVjdAogKiAgICBmb3IgdXNlIGluIHRoZSBPcGVuU1NMIFRvb2xraXQgKGh0dHA6Ly93d3cub3BlbnNzbC5vcmcvKSIKICoKICogVEhJUyBTT0ZUV0FSRSBJUyBQUk9WSURFRCBCWSBUSEUgT3BlblNTTCBQUk9KRUNUIGBgQVMgSVMnJyBBTkQgQU5ZCiAqIEVYUFJFU1NFRCBPUiBJTVBMSUVEIFdBUlJBTlRJRVMsIElOQ0xVRElORywgQlVUIE5PVCBMSU1JVEVEIFRPLCBUSEUKICogSU1QTElFRCBXQVJSQU5USUVTIE9GIE1FUkNIQU5UQUJJTElUWSBBTkQgRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSCiAqIFBVUlBPU0UgQVJFIERJU0NMQUlNRUQuICBJTiBOTyBFVkVOVCBTSEFMTCBUSEUgT3BlblNTTCBQUk9KRUNUIE9SCiAqIElUUyBDT05UUklCVVRPUlMgQkUgTElBQkxFIEZPUiBBTlkgRElSRUNULCBJTkRJUkVDVCwgSU5DSURFTlRBTCwKICogU1BFQ0lBTCwgRVhFTVBMQVJZLCBPUiBDT05TRVFVRU5USUFMIERBTUFHRVMgKElOQ0xVRElORywgQlVUCiAqIE5PVCBMSU1JVEVEIFRPLCBQUk9DVVJFTUVOVCBPRiBTVUJTVElUVVRFIEdPT0RTIE9SIFNFUlZJQ0VTOwogKiBMT1NTIE9GIFVTRSwgREFUQSwgT1IgUFJPRklUUzsgT1IgQlVTSU5FU1MgSU5URVJSVVBUSU9OKQogKiBIT1dFVkVSIENBVVNFRCBBTkQgT04gQU5ZIFRIRU9SWSBPRiBMSUFCSUxJVFksIFdIRVRIRVIgSU4gQ09OVFJBQ1QsCiAqIFNUUklDVCBMSUFCSUxJVFksIE9SIFRPUlQgKElOQ0xVRElORyBORUdMSUdFTkNFIE9SIE9USEVSV0lTRSkKICogQVJJU0lORyBJTiBBTlkgV0FZIE9VVCBPRiBUSEUgVVNFIE9GIFRISVMgU09GVFdBUkUsIEVWRU4gSUYgQURWSVNFRAogKiBPRiBUSEUgUE9TU0lCSUxJVFkgT0YgU1VDSCBEQU1BR0UuCiAqID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAqCiAqIFRoaXMgcHJvZHVjdCBpbmNsdWRlcyBjcnlwdG9ncmFwaGljIHNvZnR3YXJlIHdyaXR0ZW4gYnkgRXJpYyBZb3VuZwogKiAoZWF5QGNyeXB0c29mdC5jb20pLiAgVGhpcyBwcm9kdWN0IGluY2x1ZGVzIHNvZnR3YXJlIHdyaXR0ZW4gYnkgVGltCiAqIEh1ZHNvbiAodGpoQGNyeXB0c29mdC5jb20pLgogKgogKi8KCiBPcmlnaW5hbCBTU0xlYXkgTGljZW5zZQogLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KCi8qIENvcHlyaWdodCAoQykgMTk5NS0xOTk4IEVyaWMgWW91bmcgKGVheUBjcnlwdHNvZnQuY29tKQogKiBBbGwgcmlnaHRzIHJlc2VydmVkLgogKgogKiBUaGlzIHBhY2thZ2UgaXMgYW4gU1NMIGltcGxlbWVudGF0aW9uIHdyaXR0ZW4KICogYnkgRXJpYyBZb3VuZyAoZWF5QGNyeXB0c29mdC5jb20pLgogKiBUaGUgaW1wbGVtZW50YXRpb24gd2FzIHdyaXR0ZW4gc28gYXMgdG8gY29uZm9ybSB3aXRoIE5ldHNjYXBlcyBTU0wuCiAqIAogKiBUaGlzIGxpYnJhcnkgaXMgZnJlZSBmb3IgY29tbWVyY2lhbCBhbmQgbm9uLWNvbW1lcmNpYWwgdXNlIGFzIGxvbmcgYXMKICogdGhlIGZvbGxvd2luZyBjb25kaXRpb25zIGFyZSBhaGVhcmVkIHRvLiAgVGhlIGZvbGxvd2luZyBjb25kaXRpb25zCiAqIGFwcGx5IHRvIGFsbCBjb2RlIGZvdW5kIGluIHRoaXMgZGlzdHJpYnV0aW9uLCBiZSBpdCB0aGUgUkM0LCBSU0EsCiAqIGxoYXNoLCBERVMsIGV0Yy4sIGNvZGU7IG5vdCBqdXN0IHRoZSBTU0wgY29kZS4gIFRoZSBTU0wgZG9jdW1lbnRhdGlvbgogKiBpbmNsdWRlZCB3aXRoIHRoaXMgZGlzdHJpYnV0aW9uIGlzIGNvdmVyZWQgYnkgdGhlIHNhbWUgY29weXJpZ2h0IHRlcm1zCiAqIGV4Y2VwdCB0aGF0IHRoZSBob2xkZXIgaXMgVGltIEh1ZHNvbiAodGpoQGNyeXB0c29mdC5jb20pLgogKiAKICogQ29weXJpZ2h0IHJlbWFpbnMgRXJpYyBZb3VuZydzLCBhbmQgYXMgc3VjaCBhbnkgQ29weXJpZ2h0IG5vdGljZXMgaW4KICogdGhlIGNvZGUgYXJlIG5vdCB0byBiZSByZW1vdmVkLgogKiBJZiB0aGlzIHBhY2thZ2UgaXMgdXNlZCBpbiBhIHByb2R1Y3QsIEVyaWMgWW91bmcgc2hvdWxkIGJlIGdpdmVuIGF0dHJpYnV0aW9uCiAqIGFzIHRoZSBhdXRob3Igb2YgdGhlIHBhcnRzIG9mIHRoZSBsaWJyYXJ5IHVzZWQuCiAqIFRoaXMgY2FuIGJlIGluIHRoZSBmb3JtIG9mIGEgdGV4dHVhbCBtZXNzYWdlIGF0IHByb2dyYW0gc3RhcnR1cCBvcgogKiBpbiBkb2N1bWVudGF0aW9uIChvbmxpbmUgb3IgdGV4dHVhbCkgcHJvdmlkZWQgd2l0aCB0aGUgcGFja2FnZS4KICogCiAqIFJlZGlzdHJpYnV0aW9uIGFuZCB1c2UgaW4gc291cmNlIGFuZCBiaW5hcnkgZm9ybXMsIHdpdGggb3Igd2l0aG91dAogKiBtb2RpZmljYXRpb24sIGFyZSBwZXJtaXR0ZWQgcHJvdmlkZWQgdGhhdCB0aGUgZm9sbG93aW5nIGNvbmRpdGlvbnMKICogYXJlIG1ldDoKICogMS4gUmVkaXN0cmlidXRpb25zIG9mIHNvdXJjZSBjb2RlIG11c3QgcmV0YWluIHRoZSBjb3B5cmlnaHQKICogICAgbm90aWNlLCB0aGlzIGxpc3Qgb2YgY29uZGl0aW9ucyBhbmQgdGhlIGZvbGxvd2luZyBkaXNjbGFpbWVyLgogKiAyLiBSZWRpc3RyaWJ1dGlvbnMgaW4gYmluYXJ5IGZvcm0gbXVzdCByZXByb2R1Y2UgdGhlIGFib3ZlIGNvcHlyaWdodAogKiAgICBub3RpY2UsIHRoaXMgbGlzdCBvZiBjb25kaXRpb25zIGFuZCB0aGUgZm9sbG93aW5nIGRpc2NsYWltZXIgaW4gdGhlCiAqICAgIGRvY3VtZW50YXRpb24gYW5kL29yIG90aGVyIG1hdGVyaWFscyBwcm92aWRlZCB3aXRoIHRoZSBkaXN0cmlidXRpb24uCiAqIDMuIEFsbCBhZHZlcnRpc2luZyBtYXRlcmlhbHMgbWVudGlvbmluZyBmZWF0dXJlcyBvciB1c2Ugb2YgdGhpcyBzb2Z0d2FyZQogKiAgICBtdXN0IGRpc3BsYXkgdGhlIGZvbGxvd2luZyBhY2tub3dsZWRnZW1lbnQ6CiAqICAgICJUaGlzIHByb2R1Y3QgaW5jbHVkZXMgY3J5cHRvZ3JhcGhpYyBzb2Z0d2FyZSB3cml0dGVuIGJ5CiAqICAgICBFcmljIFlvdW5nIChlYXlAY3J5cHRzb2Z0LmNvbSkiCiAqICAgIFRoZSB3b3JkICdjcnlwdG9ncmFwaGljJyBjYW4gYmUgbGVmdCBvdXQgaWYgdGhlIHJvdWluZXMgZnJvbSB0aGUgbGlicmFyeQogKiAgICBiZWluZyB1c2VkIGFyZSBub3QgY3J5cHRvZ3JhcGhpYyByZWxhdGVkIDotKS4KICogNC4gSWYgeW91IGluY2x1ZGUgYW55IFdpbmRvd3Mgc3BlY2lmaWMgY29kZSAob3IgYSBkZXJpdmF0aXZlIHRoZXJlb2YpIGZyb20gCiAqICAgIHRoZSBhcHBzIGRpcmVjdG9yeSAoYXBwbGljYXRpb24gY29kZSkgeW91IG11c3QgaW5jbHVkZSBhbiBhY2tub3dsZWRnZW1lbnQ6CiAqICAgICJUaGlzIHByb2R1Y3QgaW5jbHVkZXMgc29mdHdhcmUgd3JpdHRlbiBieSBUaW0gSHVkc29uICh0amhAY3J5cHRzb2Z0LmNvbSkiCiAqIAogKiBUSElTIFNPRlRXQVJFIElTIFBST1ZJREVEIEJZIEVSSUMgWU9VTkcgYGBBUyBJUycnIEFORAogKiBBTlkgRVhQUkVTUyBPUiBJTVBMSUVEIFdBUlJBTlRJRVMsIElOQ0xVRElORywgQlVUIE5PVCBMSU1JVEVEIFRPLCBUSEUKICogSU1QTElFRCBXQVJSQU5USUVTIE9GIE1FUkNIQU5UQUJJTElUWSBBTkQgRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSIFBVUlBPU0UKICogQVJFIERJU0NMQUlNRUQuICBJTiBOTyBFVkVOVCBTSEFMTCBUSEUgQVVUSE9SIE9SIENPTlRSSUJVVE9SUyBCRSBMSUFCTEUKICogRk9SIEFOWSBESVJFQ1QsIElORElSRUNULCBJTkNJREVOVEFMLCBTUEVDSUFMLCBFWEVNUExBUlksIE9SIENPTlNFUVVFTlRJQUwKICogREFNQUdFUyAoSU5DTFVESU5HLCBCVVQgTk9UIExJTUlURUQgVE8sIFBST0NVUkVNRU5UIE9GIFNVQlNUSVRVVEUgR09PRFMKICogT1IgU0VSVklDRVM7IExPU1MgT0YgVVNFLCBEQVRBLCBPUiBQUk9GSVRTOyBPUiBCVVNJTkVTUyBJTlRFUlJVUFRJT04pCiAqIEhPV0VWRVIgQ0FVU0VEIEFORCBPTiBBTlkgVEhFT1JZIE9GIExJQUJJTElUWSwgV0hFVEhFUiBJTiBDT05UUkFDVCwgU1RSSUNUCiAqIExJQUJJTElUWSwgT1IgVE9SVCAoSU5DTFVESU5HIE5FR0xJR0VOQ0UgT1IgT1RIRVJXSVNFKSBBUklTSU5HIElOIEFOWSBXQVkKICogT1VUIE9GIFRIRSBVU0UgT0YgVEhJUyBTT0ZUV0FSRSwgRVZFTiBJRiBBRFZJU0VEIE9GIFRIRSBQT1NTSUJJTElUWSBPRgogKiBTVUNIIERBTUFHRS4KICogCiAqIFRoZSBsaWNlbmNlIGFuZCBkaXN0cmlidXRpb24gdGVybXMgZm9yIGFueSBwdWJsaWNhbGx5IGF2YWlsYWJsZSB2ZXJzaW9uIG9yCiAqIGRlcml2YXRpdmUgb2YgdGhpcyBjb2RlIGNhbm5vdCBiZSBjaGFuZ2VkLiAgaS5lLiB0aGlzIGNvZGUgY2Fubm90IHNpbXBseSBiZQogKiBjb3BpZWQgYW5kIHB1dCB1bmRlciBhbm90aGVyIGRpc3RyaWJ1dGlvbiBsaWNlbmNlCiAqIFtpbmNsdWRpbmcgdGhlIEdOVSBQdWJsaWMgTGljZW5jZS5dCiAqLwoKCklTQyBsaWNlbnNlIHVzZWQgZm9yIGNvbXBsZXRlbHkgbmV3IGNvZGUgaW4gQm9yaW5nU1NMOgoKLyogQ29weXJpZ2h0IChjKSAyMDE1LCBHb29nbGUgSW5jLgogKgogKiBQZXJtaXNzaW9uIHRvIHVzZSwgY29weSwgbW9kaWZ5LCBhbmQvb3IgZGlzdHJpYnV0ZSB0aGlzIHNvZnR3YXJlIGZvciBhbnkKICogcHVycG9zZSB3aXRoIG9yIHdpdGhvdXQgZmVlIGlzIGhlcmVieSBncmFudGVkLCBwcm92aWRlZCB0aGF0IHRoZSBhYm92ZQogKiBjb3B5cmlnaHQgbm90aWNlIGFuZCB0aGlzIHBlcm1pc3Npb24gbm90aWNlIGFwcGVhciBpbiBhbGwgY29waWVzLgogKgogKiBUSEUgU09GVFdBUkUgSVMgUFJPVklERUQgIkFTIElTIiBBTkQgVEhFIEFVVEhPUiBESVNDTEFJTVMgQUxMIFdBUlJBTlRJRVMKICogV0lUSCBSRUdBUkQgVE8gVEhJUyBTT0ZUV0FSRSBJTkNMVURJTkcgQUxMIElNUExJRUQgV0FSUkFOVElFUyBPRgogKiBNRVJDSEFOVEFCSUxJVFkgQU5EIEZJVE5FU1MuIElOIE5PIEVWRU5UIFNIQUxMIFRIRSBBVVRIT1IgQkUgTElBQkxFIEZPUiBBTlkKICogU1BFQ0lBTCwgRElSRUNULCBJTkRJUkVDVCwgT1IgQ09OU0VRVUVOVElBTCBEQU1BR0VTIE9SIEFOWSBEQU1BR0VTCiAqIFdIQVRTT0VWRVIgUkVTVUxUSU5HIEZST00gTE9TUyBPRiBVU0UsIERBVEEgT1IgUFJPRklUUywgV0hFVEhFUiBJTiBBTiBBQ1RJT04KICogT0YgQ09OVFJBQ1QsIE5FR0xJR0VOQ0UgT1IgT1RIRVIgVE9SVElPVVMgQUNUSU9OLCBBUklTSU5HIE9VVCBPRiBPUiBJTgogKiBDT05ORUNUSU9OIFdJVEggVEhFIFVTRSBPUiBQRVJGT1JNQU5DRSBPRiBUSElTIFNPRlRXQVJFLiAqLwoKClRoZSBjb2RlIGluIHRoaXJkX3BhcnR5L2ZpYXQgY2FycmllcyB0aGUgTUlUIGxpY2Vuc2U6CgpDb3B5cmlnaHQgKGMpIDIwMTUtMjAxNiB0aGUgZmlhdC1jcnlwdG8gYXV0aG9ycyAoc2VlCmh0dHBzOi8vZ2l0aHViLmNvbS9taXQtcGx2L2ZpYXQtY3J5cHRvL2Jsb2IvbWFzdGVyL0FVVEhPUlMpLgoKUGVybWlzc2lvbiBpcyBoZXJlYnkgZ3JhbnRlZCwgZnJlZSBvZiBjaGFyZ2UsIHRvIGFueSBwZXJzb24gb2J0YWluaW5nIGEgY29weQpvZiB0aGlzIHNvZnR3YXJlIGFuZCBhc3NvY2lhdGVkIGRvY3VtZW50YXRpb24gZmlsZXMgKHRoZSAiU29mdHdhcmUiKSwgdG8gZGVhbAppbiB0aGUgU29mdHdhcmUgd2l0aG91dCByZXN0cmljdGlvbiwgaW5jbHVkaW5nIHdpdGhvdXQgbGltaXRhdGlvbiB0aGUgcmlnaHRzCnRvIHVzZSwgY29weSwgbW9kaWZ5LCBtZXJnZSwgcHVibGlzaCwgZGlzdHJpYnV0ZSwgc3VibGljZW5zZSwgYW5kL29yIHNlbGwKY29waWVzIG9mIHRoZSBTb2Z0d2FyZSwgYW5kIHRvIHBlcm1pdCBwZXJzb25zIHRvIHdob20gdGhlIFNvZnR3YXJlIGlzCmZ1cm5pc2hlZCB0byBkbyBzbywgc3ViamVjdCB0byB0aGUgZm9sbG93aW5nIGNvbmRpdGlvbnM6CgpUaGUgYWJvdmUgY29weXJpZ2h0IG5vdGljZSBhbmQgdGhpcyBwZXJtaXNzaW9uIG5vdGljZSBzaGFsbCBiZSBpbmNsdWRlZCBpbiBhbGwKY29waWVzIG9yIHN1YnN0YW50aWFsIHBvcnRpb25zIG9mIHRoZSBTb2Z0d2FyZS4KClRIRSBTT0ZUV0FSRSBJUyBQUk9WSURFRCAiQVMgSVMiLCBXSVRIT1VUIFdBUlJBTlRZIE9GIEFOWSBLSU5ELCBFWFBSRVNTIE9SCklNUExJRUQsIElOQ0xVRElORyBCVVQgTk9UIExJTUlURUQgVE8gVEhFIFdBUlJBTlRJRVMgT0YgTUVSQ0hBTlRBQklMSVRZLApGSVRORVNTIEZPUiBBIFBBUlRJQ1VMQVIgUFVSUE9TRSBBTkQgTk9OSU5GUklOR0VNRU5ULiBJTiBOTyBFVkVOVCBTSEFMTCBUSEUKQVVUSE9SUyBPUiBDT1BZUklHSFQgSE9MREVSUyBCRSBMSUFCTEUgRk9SIEFOWSBDTEFJTSwgREFNQUdFUyBPUiBPVEhFUgpMSUFCSUxJVFksIFdIRVRIRVIgSU4gQU4gQUNUSU9OIE9GIENPTlRSQUNULCBUT1JUIE9SIE9USEVSV0lTRSwgQVJJU0lORyBGUk9NLApPVVQgT0YgT1IgSU4gQ09OTkVDVElPTiBXSVRIIFRIRSBTT0ZUV0FSRSBPUiBUSEUgVVNFIE9SIE9USEVSIERFQUxJTkdTIElOIFRIRQpTT0ZUV0FSRS4K"  # noqa
                                }
                            }
                        }
                    ],
                    "purl": "pkg:cargo/ring@0.17.8",
                    "externalReferences": [
                        {
                            "type": "other",
                            "url": "ring_core_0_17_8"
                        },
                        {
                            "type": "vcs",
                            "url": "https://github.com/briansmith/ring"
                        }
                    ]
                }
            ]
        }

        parser = SbomJsonParser(SBOM)
        bom = Bom.from_parser(parser=parser)

        self.assertIsNotNone(bom)
        self.assertIsNotNone(bom.metadata)
        self.assertIsNotNone(bom.components)
        self.assertEqual(1, len(bom.components))
        comp: Component = bom.components[0]
        self.assertEqual("ring", comp.name)
        self.assertEqual("0.17.8", comp.version)
        self.assertEqual(1, len(comp.hashes))
        self.assertEqual(1, len(comp.licenses))
        lchoice: LicenseChoice = comp.licenses[0]
        self.assertIsNotNone(lchoice.license)
        self.assertIsNone(lchoice.expression)
        if lchoice.license:  # only because of mypy
            self.assertEqual("Unknown", lchoice.license.name)
            self.assertIsNone(lchoice.license.text)
            if lchoice.license.text:  # only because of mypy
                self.assertIsNotNone(lchoice.license.text)
                self.assertEqual("base64", lchoice.license.text.encoding)
                self.assertTrue(lchoice.license.text.content.startswith("Tm90ZSB0aGF0IGl"))

    def test_license_text_not_valid_cyclonedx(self) -> None:
        SBOM = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.3",
            "version": 1,
            "serialNumber": "urn:uuid:102596b3-881c-44f1-b12e-19ea42ab73e8",
            "metadata": {
                "timestamp": "2024-10-04T08:00:00.693380684Z",
                "tools": [
                    {
                        "vendor": "CycloneDX",
                        "name": "cargo-cyclonedx",
                        "version": "0.5.0"
                    }
                ],
            },
            "components": [
                {
                    "type": "library",
                    "bom-ref": "registry+https://github.com/rust-lang/crates.io-index#ring@0.17.8",
                    "name": "ring",
                    "version": "0.17.8",
                    "description": "Safe, fast, small crypto using Rust.",
                    "scope": "required",
                    "hashes": [
                        {
                            "alg": "SHA-256",
                            "content": "c17fa4cb658e3583423e915b9f3acc01cceaee1860e33d59ebae66adc3a2dc0d"
                        }
                    ],
                    "licenses": [
                        {
                            "license": {
                                "name": "Apache Software License, 2.0",
                                "text": "This is some text - not CycloneDX spec >= 1.2 compliant"
                            }
                        }
                    ],
                    "purl": "pkg:cargo/ring@0.17.8",
                    "externalReferences": [
                        {
                            "type": "other",
                            "url": "ring_core_0_17_8"
                        },
                        {
                            "type": "vcs",
                            "url": "https://github.com/briansmith/ring"
                        }
                    ]
                }
            ]
        }

        parser = SbomJsonParser(SBOM)
        bom = Bom.from_parser(parser=parser)

        self.assertIsNotNone(bom)
        self.assertIsNotNone(bom.metadata)
        self.assertIsNotNone(bom.components)
        self.assertEqual(1, len(bom.components))
        comp: Component = bom.components[0]
        self.assertEqual("ring", comp.name)
        self.assertEqual("0.17.8", comp.version)
        self.assertEqual(1, len(comp.hashes))
        self.assertEqual(1, len(comp.licenses))
        lchoice: LicenseChoice = comp.licenses[0]
        self.assertIsNotNone(lchoice.license)
        self.assertIsNone(lchoice.expression)
        if lchoice.license:  # only because of mypy
            self.assertIsNotNone(lchoice.license.name)
            self.assertEqual("Apache Software License, 2.0", lchoice.license.name)
            self.assertIsNone(lchoice.license.id)
            self.assertIsNone(lchoice.license.text)
            if lchoice.license.text:  # only because of mypy
                self.assertEqual("This is some text - not CycloneDX spec >= 1.2 compliant",
                                 lchoice.license.text.content)
                self.assertEqual("text/plain", lchoice.license.text.content_type)
                self.assertEqual(None, lchoice.license.text.encoding)


if __name__ == "__main__":
    APP = TestSbomLicenseVariants()
    APP.setUp()
    APP.test_license_text_not_valid_cyclonedx()
