<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->

# Software Clearing Automation

In the very beginning there was no available format for a bill of material (SBOM),
so we created our own format. But we still kept an eye on other existing SBOM
formats. When CycloneDX released their SBOM format, version 1.3 we decided to
use this format for all future use cases.

## New SBOM Format (CycloneDX based)

Please see [CycloneDX](https://github.com/CycloneDX) and especially
[CycloneDX SBOM specification](https://github.com/CycloneDX/specification) for the original
CycloneDX SBOM format. In this document we will only explain our enhancements and which properties
are mandatory for our processing.

CaPyCLI supports CycloneDX only in **JSON format.**

### CycloneDX SBOM Properties used by CaPyCLI

| Key                                        | Description                    |
| -------------------------------------------| ------------------------------ |
| bomFormat                                  | expected value is CycloneDX    |
| specVersion                                | expected value is 1.x          |
| metadata/tools                             | tool that created the SBOM     |
| component/name                             | name of the component          |
| component/group                            | (optional) group name          |
| component/version                          | component version              |
| component/purl                             | package-url                    |
| component/publisher                        | (NOT YET EVALUATED)            |
| component/description                      | (NOT YET EVALUATED)            |
| component/externalReferences/website       | component website              |
| component/externalReferences/vcs           | source code / vcs URL          |
| component/externalReferences/distribution  | (optional for source code url) |
| component/externalReferences/hashes        | (optional for src code SHA-1)  |

### CaPyCLI CycloneDX SBOM Enhancements

CycloneDX SBOM format version 1.3 and later allow a custom key-value store. That is
what we use for our CaPyCLI specific properties. We use either the official `siemens`
namespace or the `capycli` namespace.

| Key                       | Description                        |
| ------------------------- | ---------------------------------- |
| siemens:sw360Id           | SW360 ID (of a release)            |
| siemens:primaryLanguage   | programming language               |
| siemens:filename          | name of a (source) file            |
| siemens:profile           | profile/type of the SBOM           |
| capycli:componentId       | id of a component, part of mapping |
| capycli:sourceFileType    | SW360 attachment type              |
| capycli:sourceFileComment | upload comment for SW360 attachment|
| capycli:mapResult         | mapping result                     |

Example:

```code
{
      "type": "library",
      "name": "joda-time",
      "version": "2.10.5",
      "scope": "required",
      "purl": "pkg:pkg:maven/joda-time/joda-time@2.10.5",
      "externalReferences": [
        {
          "url": "https://github.com/JodaOrg/joda-time",
          "type": "website"
        },
        {
          "url": "https://github.com/JodaOrg/joda-time/archive/refs/tags/v2.10.5.zip",
          "type": "distribution",
          "comment": "source archive (download location)""
        }
      ],
      "properties": [
        {
          "name": "siemens:primaryLanguage",
          "value": "Java"
        },
        {
          "name": "siemens:sw360Id",
          "value": "f9159fde78553c2ba192b7fa8e8c2033"
        }
      ]
    }
```

### Open Issues

* There is no clear definition on how the property `group` is used.
  Assume the package-url is `pkg:npm/%40simpl/sishell-icons@6.8.1`.
  Is then group = `@simpl` and name = `sishell-icons`? Or is group = `@simpl`
  and name = `@simpl/sishell-icons`? We found evidence for both variants.
* Is there a Python library to parse CycloneDX SBOMs? On GitHub we were
  not able to find code for that...

## Original CaPyCLI SBOM Format (deprecated)

The format of the JSON SBOM file is a list of
component objects. Each component object contains
the fields

* **Name** - name of the component (**mandatory**)
* **Version** - version of the component (**mandatory**)
* **Language** - programming language. Needed for example for the component ```tar``` to
  determine whether the C/C++, Java or JavaScript version is meant.
* **SourceUrl** - informal URL of source download page
* **SourceFile** - name of the source file
* **SourceFileUrl** - URL directly pointing to source file
* **SourceFileHash** - hash of the source file
* **SourceFileType** - SW360 attachment type ("SOURCE" (default) or "SOURCE_SELF"
 (for self-made sources))
* **SourceFileComment** - upload comment for SW360 attachment
* **BinaryFile** - name of the binary file
* **BinaryFileUrl** - URL of the binary file
* **BinaryFileHash** - hash of the binary file
* **ProjectSite** - project/component/community web site
* **RepositoryType** - repository type (nuget, npm, maven, package-url)
* **RepositoryId** - repository id (within the specified repository)
* **Sw360Id** - if already known. Will be filled in when the release has been found on SW360

The more (meta) information is available, the better are the chances to find the component
on SW360. We can search on SW360 directly for attachments (files)
with a specific hash and we can also search for a repository id.

Some of the data is also required when a new component or release
needs to be created on SW360:

### Mandatory information for components

* name
* type (OSS or COTS)

### Mandatory information for releases

* name (of the component)
* version
* programming language
* source code download URL
* source code file
* vendor

### SBOM Example

Minimum information

```code
[
  {
    "Name": "Tethys.Framework",
    "Version": "4.4.0",
    "Language": "C#",
    "SourceFileUrl": "https://github.com/tngraf/Tethys.Framework/archive/v99.4.0.zip",
    "SourceFile": "Tethys.Framework-4.4.0.zip",
  },
  { ... }
]
```

Full information

```code
[
  {
    "Name": "Tethys.Framework",
    "Version": "4.4.0",
    "Language": "C#",
    "SourceUrl": "https://github.com/tngraf/Tethys.Framework/releases/tag/v4.4.0",
    "SourceFileUrl": "https://github.com/tngraf/Tethys.Framework/archive/v99.4.0.zip",
    "SourceFile": "Tethys.Framework.4.4.0.zip",
    "SourceFileHash": "08150815081508150815081508150815",
    "SourceFileType": "SOURCE",
    "SourceFileComment": "source archive verified by Development",
    "BinaryFile": "tethys.framework.4.4.0.nupkg",
    "BinaryFileHash": "7580CCDDA1E2DB1766E7627FCA508394A06A3DAF",
    "ProjectSite": "https://github.com/tngraf/Tethys.Framework",
    "RepositoryType": "nuget-id",
    "RepositoryId": "Tethys.Framework.4.4.0",
    "Sw360Id": "44ce6d4c8b1b84baa450f29e53001702"
  },
  { ... }
]
```

### Filter Example

Minimum Information

```code
{
  Components": [
    {
      "component": {
        "Name": "black"
      },
      "Mode": "remove"
    },
    {
      "component": {
        "Name": "sw360"
      },
      "Mode": "add"
    }
  ]
}
```
