<!--
# SPDX-FileCopyrightText: (c) 2018-2024 Siemens
# SPDX-License-Identifier: MIT
-->

# CaPyCli - SBOM Mapping

Mapping an existing bill of materials to the data available on SW360 is one
of the more magical parts of CaPyCLI.

The current approach is checking the following properties in this order:

1. unique id, i.e. checking external ids like the `package-url`
2. check for name **and** version
3. check for unique(?) source file hash
4. check source filename
5. check for name and **any** version
6. look for similar names

CaPyCLI creates as result of the SBOM mapping an extended SBOM file. This SBOM file
contains the original entries and **all** matching entries. The `Result` value
informs about the mapping result:

* **`INVALID` (0)** => Invalid SBOM entry, could not get processed
* **`FULL_MATCH_BY_ID` (1)** => Full match by identifier
* **`FULL_MATCH_BY_HASH` (2)** => Full match by source file hash
* **`FULL_MATCH_BY_NAME_AND_VERSION` (3)** => Full match by name and version
* **`MATCH_BY_FILENAME` (4)** => Match by source code filename
* **`GOOD_MATCH_FOUND`** == `MATCH_BY_FILENAME` => successfully found a sifficiently good match
* **`MATCH_BY_NAME` (5)** => Component found, but no version match
* **`SIMILAR_COMPONENT_FOUND` (6)** => Component with similar name found, no version check done
* **`NO_MATCH` (100)** => Component was not found

In general you can say that the lower the number, the better the match.

## Example 1: Very Simple, Full Match

The input SBOM contains two releases:

* AbrarJahin.DiffMatchPatch, 0.1.0
  * package-url = pkg:nuget/AbrarJahin.DiffMatchPatch@0.1.0
* Tethys.Logging, 1.4.2
  * package-url = pkg:nuget/Tethys.Logging@1.4.2

Run `bom map` command

Console output

```shell
    Found component f2d5e8de3f216ab5ef88896f69016852 via purl for release 0.1.0
    Found component eaba2f0416e000e8ca5b2ccb4400633e via purl

Mapping result:
  Full match by id, AbrarJahin.DiffMatchPatch, 0.1.0 => AbrarJahin.DiffMatchPatch, 0.1.0, f2d5e8de3f216ab5ef88896f69017441
  Full match by id, Tethys.Logging, 1.4.2 => Tethys.Logging, 1.4.2, 4564c337d7b0f9751d32fde2a712fbbe
  Full match by id, .Net Runtime, 5.0.12 => .NET Runtime, 5.0.12, 530f0d0d7ef84c3f8aa4e9e907c91a3a

Total releases    = 2
  Full matches    = 2
  Name matches    = 0
  Similar matches = 0
  No match        = 0
```

Contents of the resulting SBOM

* AbrarJahin.DiffMatchPatch, 0.1.0
  * result = 1 (FULL_MATCH_BY_ID, i.e. match by package-url)
  * sw360id = f2d5e8de3f216ab5ef88896f69017441
* Tethys.Logging, 1.4.2
  * result = 1 (FULL_MATCH_BY_ID, i.e. match by package-url)
  * sw360id = 4564c337d7b0f9751d32fde2a712fbbe

=> All releases have been found  
=> The output bom of `bom map` contains exactly two entries  
   and can be directly used to create a project on SW360  
=> All done

## Example 2: Simple, No Full Match

The input SBOM contains two releases:

* AbrarJahin.DiffMatchPatch, 0.1.0
  * package-url = pkg:nuget/AbrarJahin.DiffMatchPatch@0.1.0
* Tethys.Logging, 1.4.3
  * package-url = pkg:nuget/Tethys.Logging@1.4.2

### Run `bom map` command

```shell
capycli bom map -i bom.json --nocache -o bom_mapped.json
```

Console output

```shell
Mapping result:
  Full match by name and version, AbrarJahin.DiffMatchPatch, 0.1.0 => AbrarJahin.DiffMatchPatch, 0.1.0
  No match, Tethys.Logging, 1.4.3

Total releases    = 2
  Full matches    = 0
  Name matches    = 1
  Similar matches = 0
  No match        = 1

No unique mapping found - manual action needed!
```

The contents of the resulting SBOM depends on the optional
parameters `mode` and `-all`.

### Run `bom map` command, `-all` specified

```shell
capycli bom map -i bom.json --nocache -o bom_mapped.json -all
```

Console output

```shell

Mapping result:
  Full match by id, AbrarJahin.DiffMatchPatch, 0.1.0 => AbrarJahin.DiffMatchPatch, 0.1.0, 
  Match by name, Tethys.Logging, 1.4.3 => Tethys.Logging, 1.6.1 (and 5 others)

Total releases    = 2
  Full matches    = 1
  Name matches    = 1
  Similar matches = 0
  No match        = 0

No unique mapping found - manual action needed!
```

### Contents of the resulting SBOM (`mode` not set, `-all` not set)

* AbrarJahin.DiffMatchPatch, 0.1.0
  * result = 1 (FULL_MATCH_BY_ID, i.e. match by package-url)
  * sw360id = f2d5e8de3f216ab5ef88896f69017441
* Tethys.Logging, 1.4.3
  * result = 100 (NO_MATCH)

=> One release has been found, for the other releases there was no match.
=> The output SBOM of `bom map` contains exactly **two** entries.  

   This SBOM can get fed into `bom CreateComponents` or `bom CreateReleases` to create
   the missing release 1.4.3.
   The updated SBOM of the release creation can then  get used to to create a project
   on SW360.

 => Done

### Contents of the resulting SBOM (`mode` not set, `-all` set)

CaPyCLI will also report matches per name, but not per version:

* AbrarJahin.DiffMatchPatch, 0.1.0
  * result = 1 (FULL_MATCH_BY_ID, i.e. match by package-url)
  * sw360id = f2d5e8de3f216ab5ef88896f69017441
* Tethys.Logging, 1.4.3
  * result = 100 (NO_MATCH)
* Tethys.Logging, 1.6.1
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = ce56cdbd89714def894e572b1a5b5937
* Tethys.Logging, 1.4.2
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = 4564c337d7b0f9751d32fde2a712fbbe
* Tethys.Logging, 1.0
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = eaba2f0416e000e8ca5b2ccb440071c6
* Tethys.Logging, 1.6.0
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = 0b38c2783b33ff58a4c12a1bbbca0e07
* Tethys.Logging, 1.4.0
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = 95a05a6fff469a1aebe03c0233002fb0

=> One release has been found, for the other releases there was only a match by name  
=> The output SBOM of `bom map` contains exactly **seven** entries.  
   **Manual intervention is needed: the user needs to decide whether to use one of the existing  
   releases of Tethys.Logging or to force CaPyCLI to create release 1.4.3 which does not
   yet exist.**  
   The user needs to remove all releases that should not get considered.

   One option would be to use the latest clearing version of Tethys.Logging. In this case
   the SBOM needs to be edited to show

* AbrarJahin.DiffMatchPatch, 0.1.0
  * sw360id = f2d5e8de3f216ab5ef88896f69017441
* Tethys.Logging, 1.6.1
  * sw360id = ce56cdbd89714def894e572b1a5b5937
   This SBOM can then directly get used to to create a project on SW360

   Another option would be to force the creation of Tethys.Logging, 1.4.3. In this case
   the SBOM needs to be edited to show

* AbrarJahin.DiffMatchPatch, 0.1.0
  * sw360id = f2d5e8de3f216ab5ef88896f69017441
* Tethys.Logging, 1.4.3

   This SBOM can get fed into `bom CreateComponents` or `bom CreateReleases` to create
   the missing release 1.4.3.
   The updated SBOM of the release creation can then  get used to to create a project
   on SW360.

 => Done

### Contents of the resulting SBOM (`mode` = "found")

* AbrarJahin.DiffMatchPatch, 0.1.0
  * result = 1 (FULL_MATCH_BY_ID, i.e. match by package-url)
  * sw360id = f2d5e8de3f216ab5ef88896f69017441

=> One release has been found, for the other releases there was only a match by name  
=> The output SBOM of `bom map` contains exactly **one** entry.  
=> The resulting SBOM can be used to create/update a project with only the components
that have been found on SW360.

### Contents of the resulting SBOM (`mode` = notfound, `-all` not set)

* Tethys.Logging, 1.4.3
  * result = 100 (NO_MATCH)

=> The output SBOM of `bom map` contains exactly **one** entry.  
   This is the single component that could not get matched.  

### Contents of the resulting SBOM (`mode` = notfound, `-all` set)

* Tethys.Logging, 1.4.3
  * result = 100 (NO_MATCH)
* Tethys.Logging, 1.6.1
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = ce56cdbd89714def894e572b1a5b5937
* Tethys.Logging, 1.4.2
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = 4564c337d7b0f9751d32fde2a712fbbe
* Tethys.Logging, 1.0
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = eaba2f0416e000e8ca5b2ccb440071c6
* Tethys.Logging, 1.6.0
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = 0b38c2783b33ff58a4c12a1bbbca0e07
* Tethys.Logging, 1.4.0
  * result = 5 (MATCH_BY_NAME)  
  * sw360id = 95a05a6fff469a1aebe03c0233002fb0

=> The output SBOM of `bom map` contains exactly **six** entries.  
   These are the component that could not get matched and potential candidates.  
   **Manual intervention is needed: the user needs to decide whether to use one of the existing  
   releases of Tethys.Logging or to force CaPyCLI to create release 1.4.3 which does not
   yet exist.**  
   The user needs to remove all releases that should not get considered.

## Rationale

The rationale for the behavior to have the output SBOM of the mapping process contain
**all** findings is  
a) the user should have **the choice** to decided which component version to use  
b) the user should be forced to consider **reuse** of already cleared components  
c) it should not be needed to search manually SW360
