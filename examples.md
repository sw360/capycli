<!--
# SPDX-FileCopyrightText: (c) 2018-2024 Siemens
# SPDX-License-Identifier: MIT
-->

# CaPyCli - Clearing Automation Python Command Line Tool

Python 3 scripts to allow clearing automation.

## Examples

### Dependency management

#### Determine dependencies for a NuGet project

Command:

```sh
capycli getdependencies nuget -i csharp_diff.csproj -o csharp_bom.json
```

Result:

```sh
CaPyCli- Determine Nuget components/dependencies

Reading input file csharp_diff.csproj
Writing new SBOM to csharp_bom.json
  3 items written to SBOM.
```

#### Determine dependencies for a Visual Studio Solution

Command:

```sh
capycli getdependencies nuget -i some.sln -o some.json
```

Result:

```sh
CaPyCli- Determine Nuget components/dependencies

Reading input file some.sln
  Processing CliEditorEx\CliEditorEx.csproj
  Processing CommonUI\CommonUI.csproj
  Processing Siemens.Test\Siemens.Test.csproj
  Processing Siemens.CLI.Common\Siemens.CLI.Common.csproj
  Processing CommonUI.DockPanel\CommonUI.DockPanel.csproj
Writing new SBOM to csharp_bom.json
  44 items written to SBOM.
```

#### Determine dependencies for a Python project

Command:

```sh
capycli getdependencies python -i requirements.txt -o python_bom.json --search-meta-data
```

Result:

```sh
CaPyCli- Determine Python components/dependencies

Reading input file requirements.txt
Formatting package list...
Writing new SBOM to python_bom.json
  2 items written to SBOM.
```

#### Determine dependencies for a Javascript project

Command:

```sh
capycli getdependencies javascript -i package-lock.json -o javascript_bom.json
```

Result:

```sh
CaPyCli- Determine Javascript components/dependencies

Reading input file package-lock.json
Searching for metadata...
Writing new SBOM to javascript_bom.json
  2 items written to SBOM.
```

### SBOM (bill of material) handling

#### Print SBOM contents to stdout

Command:

```sh
capycli SBOM show -i .\TestData\bom_example.json
```

Result:

```sh
CaPyCli - Print SBOM contents to stdout

4 items in bill of material:

  @angular/animations, 7.2.12
  @angular/common, 7.2.12
  @angular/compiler, 7.2.12
  zrender, 4.0.7
```

#### Create a HTML page showing the SBOM

Command:

```sh
capycli bom convert -i .\TestData\bom_example.json -of html -o .\TestData\bom_example.html
```

Result:

```sh
CaPyCli - Create a HTML page showing the SBOM

Loading SBOM .\TestData\bom_example.json
Creating HTML page .\TestData\bom_example.html
```

#### Create a bill of material from a CSV file

Command:

```sh
capycli bom convert -if csv -i .\RealData\SI_CP_Name_Version.csv -of capycli -o .\RealData\SI_CP_Name_Version_bom.json
```

Result:

```sh
CaPyCli - Convert a CSV file to a SBOM

Loading CSV file .\RealData\SI_CP_Name_Version.csv and converting to SBOM...
Writing new SBOM to .\RealData\SI_CP_Name_Version_bom.json
```

#### Create a bill of material from a flat test file

Command:

```sh
capycli bom convert -if text -i .\TestData\flat_list.txt -of capycli -o .\TestData\generated_bom.json
```

Result:

```sh
CaPyCli - Convert a flat list of components to a SBOM

Loading text file .\TestData\flat_list.txt and converting to SBOM...
Writing new SBOM to .\TestData\generated_bom.json
```

#### Apply a filter on a bill of material

Command:

```sh
capycli bom filter -i .\TestData\bom_example.json -o .\TestData\filtered_bom.json
-filterfile .\TestData\filter.json -v
```

Result:

```sh
CaPyCli - Apply a filter file to a SBOM

Loading SBOM file .\TestData\bom_example.json
  4 components read from SBOM
Applying filter file .\TestData\filter.json
  Removing @angular/compiler, 7.2.12
  Adding .NET Core, 2.1
Writing new SBOM to .\TestData\filtered_bom.json
  4 components written to SBOM file
```

#### Check a given mapped bill of material against a SW360 instance

Command:

```sh
capycli bom check -i .\TestData\test_bom_mapped.json
```

Result:

```sh
CaPyCli - Check that all releases in the SBOM exist on target SW360 instance.

Loading SBOM file .\TestData\test_bom_mapped.json
  Not found Tethys.Logging, 1.4.2, 14564c337d7b0f9751d32fde2a712fbbe
  Found colorama, 0.4.1, 343b8e9076fc3fb796c34fc001451fd5
  Found diff-match-patch, 20181111, 05c30bf89a512463260b57e84da84d73
  Found diff_match_patch, 0.1.1, f2d5e8de3f216ab5ef88896f696d35d8
  Found Commander, 3.0.2, f2d5e8de3f216ab5ef88896f696d4337

5 components checked, 4 successfully found.
```

#### Check a given mapped bill of materials against the specified SW360 instance

Command:

```sh
capycli bom check -i .\TestData\test_bom_mapped.json -url https://dev.sw360.siemens.com -t PbVm3cPCdXZeSs7AUQhg
```

Result:

```sh
CaPyCli - Check that all releases in the SBOM exist on target SW360 instance.

Loading SBOM file .\TestData\test_bom_mapped.json
  Not found Tethys.Logging, 1.4.2, 14564c337d7b0f9751d32fde2a712fbbe
  Found colorama, 0.4.1, 343b8e9076fc3fb796c34fc001451fd5
  Found diff-match-patch, 20181111, 05c30bf89a512463260b57e84da84d73
  Found diff_match_patch, 0.1.1, f2d5e8de3f216ab5ef88896f696d35d8
  Found Commander, 3.0.2, f2d5e8de3f216ab5ef88896f696d4337

5 components checked, 4 successfully found.
```

#### Map a bill of materials to SW360 (online) and print result to screen

This will search for the SBOM items in SW360, using the component names and versions. If
you specify "-o", an updated SBOM will be written adding the found release data together
with the "MapResult" (1..4: exact release match, 5/6: matches by component, 100: not found).

If your SBOM includes **[package-urls](https://github.com/package-url/purl-spec/)**, capycli will
first retrieve a complete list of SW360 entries with the external id "package-url" and try to
identify components and releases using these rules:

* all package-urls from SW360 and your SBOM will be decoded before matching (purl encoding is
  not unique)
* qualifiers (like `?type=source`) are currently ignored in package-url matching
* to identify a release, the complete package-url is used
* components in SW360 can either be identified by a package-url in the component
  entry - or if this is not set, by package-urls from their releases (after stripping versions)
* whenever there is some ambiguity in SW360 package-url entries (for example, two different
  SW360 components use the same package-url), package-urls for those entries will be ignored.

If there's no good release match, but a component match via package-url, the component id
will be added to the updated SBOM for subsequent steps like `bom createreleases`.

Additionally, two special output files can be created: a map result file ("-mr") containing
original SBOM items and the corresponding matches and a mapping overview ("-ov") with summary
information. These files can be converted to HTML/Excel using the "mapping" and "moverview"
commands (see below).

Note that the online mapping doesn't find all possible matches. For more results, consider
using the cached search described in the next section.

Command:

```sh
capycli bom map -i .\TestData\test_bom.json --nocache
```

Result:

```sh
CaPyCli - Map a given SBOM to data on SW360

Loading SBOM file .\TestData\test_bom.json
No cached releases available!

Do mapping...
  Tethys.Logging, 1.4.2
  colorama, 0.4.1
  colorama, 0.44.1
  diff_match_patch, 0.1.1
  commander, 3.0.2

Mapping result:
 Full match by id, Tethys.Logging, 1.4.2 => Tethys.Logging, 1.4.2, 4564c337d7b...
 Full match by name and version, colorama, 0.4.1 => colorama, 0.4.1, 343b8e9076f...
 Match by name, colorama, 0.44.1 => colorama, 0.3.7-1.debian, 287e78e1e72f67e2... (and 4 others)
 Full match by id, diff_match_patch, 0.1.1 => diff_match_patch, 0.1.1, f2d5e8de3f21....
 Full match by id, commander, 3.0.2 => Commander, 3.0.2, f2d5e8de3f216ab5ef88896f6...

Total releases    = 5
  Full matches    = 4
  Name matches    = 1
  Similar matches = 0
  No match        = 0

 Creating updated SBOM .\TestData\test_bom_updated.json
No unique mapping found - manual action needed!
```

#### Map a bill of material to SW360 (using cached data)

This works like the online search described above, but will use an offline cache instead of
SW360 calls for searching. A cache of SW360 releases must either already exist or will be
generated (which currently takes 1-2 hours to complete).

In contrast to the online search described above, the cached search will compare the SBOM
items to all releases in the cache and can thus also identify SW360 releases by additional criteria
like source file hashes or file names.

Please note that the cached search might still perform online calls, for example when searching
for package urls (if included in SBOM), which will always use the latest online data.

Command:

```sh
capycli bom map -i .\TestData\test_bom.json -o .\TestData\test_bom_updated.json 
-ov .\TestData\mapping_overview.json -mr .\TestData\mapping_result.json
```

Result:

```sh
CaPyCli - Map a given SBOM to data on SW360

Loading SBOM file .\TestData\test_bom.json

Cachefile is  D:\Software\SWC\Python\Clearing_Automation_2.0\ComponentCache.json
  Loading cache...
  31251 cached releases read from cache file.

Do mapping...
  Tethys.Logging, 1.4.2
  colorama, 0.4.1
  colorama, 0.44.1
  diff_match_patch, 0.1.1
  commander, 3.0.2

Mapping result:
  Full match by id, Tethys.Logging, 1.4.2 => Tethys.Logging, 1.4.2, 4564c337d7b0f9751d32fde2a712fbbe
  Full match by name and version, colorama, 0.4.1 => colorama, 0.4.1, 343b8e9076fc3fb796c34fc001451fd5
  Match by name, colorama, 0.44.1 => colorama, 0.3.7, 84714c3cb952214b1251e9aea537cda9 (and 4 others)
  Full match by id, diff_match_patch, 0.1.1 => diff_match_patch, 0.1.1, f2d5e8de3f216ab5ef88896f696d35d8
  Full match by id, commander, 3.0.2 => Commander, 3.0.2, f2d5e8de3f216ab5ef88896f696d4337

Total releases    = 5
  Full matches    = 4
  Name matches    = 1
  Similar matches = 0
  No match        = 0

 Creating result overview .\TestData\mapping_overview.json
 Creating updated SBOM .\TestData\test_bom_updated.json
 Creating mapping result file .\TestData\mapping_result.json
No unique mapping found - manual action needed!
```

#### Show differences between two bills or material (BOM)

Command:

```sh
capycli bom merge .\dummy.bom .\dummy_new.bom
```

Result:

```sh
CaPyCli - Compare two SBOM files.

Loading first SBOM file .\dummy.bom
  44 components read from SBOM
Loading second SBOM file .\dummy_new.bom
  44 components read from SBOM
  Release exists in both SBOMs: Autofac, 6.2.0
  Release has been removed:    LiveCharts, 0.9.7
  Release exists in both SBOMs: LiveCharts.WinForms, 0.9.7.1
  ...
  New release:                 RazorEngine, 3.12.0
```

#### Merge two bills or material (BOM)

Command:

```sh
capycli bom merge .\dummy.bom .\dummy_new.bom .\merged_bom.json
```

Result:

```sh
CaPyCli - merge two SBOM files.

Loading first SBOM file .\dummy.bom
  44 components read from SBOM
Loading second SBOM file .\dummy_new.bom
  40 components read from SBOM
Combined SBOM with 46 written to .\merged_bom.json
```

#### Create a HTML page showing the mapping result

Command:

```sh
capycli mapping tohtml -i mapping_result.json -o mapping_result.html
```

Result:

```sh
CaPyCli - Create a HTML page showing the mapping result

Loading mapping result mapping_result.json
Creating HTML page mapping_result.html
```

#### Create a HTML page showing the mapping result overview

Command:

```sh
capycli moverview tohtml -i mapping_overview.json -o mapping_overview.html
```

Result:

```sh
CaPyCli - Create a HTML page showing the mapping overview

Loading mapping overview mapping_overview.json
Creating HTML page mapping_overview.html
```

#### Create an Excel sheet showing the mapping result

Command:

```sh
capycli mapping toxlsx -i mapping_result.json -o mapping_result.xlsx
```

Result:

```sh
CaPyCli - Create an Excel sheet showing the mapping result

Loading mapping result mapping_result.json
Creating HTML page mapping_result.xlsx
```

#### Create an Excel sheet showing the mapping result overview

Command:

```sh
capycli moverview toxlsx -i mapping_overview.json -o mapping_overview.xlsx
```

Result:

```sh
CaPyCli - Create an Excel sheet showing the mapping overview

Loading mapping overview mapping_overview.json
Creating Excel sheet mapping_overview.xlsx
```

### Project Management

#### Find a project by name (and version)

Command:

```sh
capycli project find -name "tr-card"
```

Result:

```sh
CaPyCli - Find a project by name

  Searching for projects by name
    TR-Card, 1.0 => ID = ff697cd18fe178b26fc601b60e00fcdf
```

#### Show a project

Command:

```sh
capycli project show -name "tr-card" -version "1.0"
```

Result:

```sh
CaPyCli - Show project details

  Searching for project...
  Project name: TR-Card, 1.0
  Project responsible: john.doe@siemens.com
  Project owner: john.doe@siemens.com
  Clearing state: IN_PROGRESS

    No linked projects

  Components:
    AngularJS, 1.7.9 = SPECIFIC
    MongoDB, 4.0.10 = SPECIFIC
    OTP, 22.2 = SPECIFIC
    RabbitMQ, 3.8.2 = OPEN
```

#### Checks whether all prerequisites for a successful software clearing are fulfilled

This will perform a number of sanity checks for the linked releases in a
project.

If a SBOM is provided as input and specifies "SourceFileHash" for the items, it
will verify that SHA1 hashes in SW360 match your SBOM. The hash information will
be added by `bom downloadsources` or you can add it to your SBOM by yourself.
Your SBOM shall also be updated with all release IDs etc, for example by
re-running `bom map` before calling `project prerequisites`.

Command:

```sh
capycli project prerequisites -name "tr-card" -version "1.0"
```

Result:

```sh
CaPyCli - Checks whether all prerequisites for a successful software clearing are fulfilled
  Searching for projects
  Project name: TR-Card, 1.0
  Clearing state: CLOSED
  Project owner: john.doe@siemens.com
  Project responsible: john.doe@siemens.com
  Security responsible(s): thomas.graf@siemens.com john.doe@siemens.com
  Tag: SI SSP

  Linked projects:
    BT LMS License Management System (Windows Client), 2.3

  Components:
    MVVM Light Toolkit, 5.3.0: SPECIFIC
      Download URL: https://mvvmlight.codeplex.com/SourceControl/changeset/view/ff4254690fed
      Programming language: C#
      Source code available.
      No component management id (NuGet, Maven, NPM, etc.) specified!

    Tethys.Framework, 4.3.1: SPECIFIC
      Download URL: https://github.com/tngraf/Tethys.Framework
      Programming language: C#
      Source code available.
      component management id: {'nuget-id': 'tethys.framework.4.3.1'}

    ...
```

#### Show licenses of all cleared components

Command:

```sh
capycli project licenses -name "tr-card" -version "1.0"
```

Result:

```sh
CaPyCli - Show licenses of all cleared compponents.
  Searching for project...
  Project name: TR-Card, 1.0
  Project owner: john.doe@siemens.com
  Clearing state: CLOSED

Components:
  Scanning 14 releases.

  ApplicationInsights, 2.5.1
   MIT

  Json.NET, 10.0.3
   MIT BSD-3-Clause
  ...
  Microsoft.Windows.Shell, 3.0.1
   Ms-PL
```

#### Get license info of all project components

Command:

```sh
capycli project getlicenseinfo -name "tr-card" -version "1.0" -dest .\temp -o rdm_config.json
```

Result:

```sh
CaPyCli - Get license info on all project components

  Searching for project...

  Components:
    MVVM Light Toolkit 5.3.0
    Tethys.Framework 4.3.1
    Microsoft .NET Framework 4.7.2
    ApplicationInsights 2.5.1
    Json.NET 10.0.3
    Feig SDK 04.06.10
    MvvmDialogs 4.0
    Visual C++ Redistributable 2010
    System.Diagnostics.DiagnosticSource 4.4.1
    Autofac 4.6.2
    NLog 4.1
    Common.Logging 3.4.1
    Microsoft.Windows.Shell 3.0.1
    MigraDoc 1.32

  Writing Readme_OSS config file rdm_config.json
```

#### Create a Readme_OSS document for a project

Command:

```sh
capycli project createreadme -i rdm_config.json -o Readme_OSS.html
```

Result:

```sh
CaPyCli - Create a Readme_OSS

  Reading config file .\TestData\rdm_config.json
  Reading CLI files...
    Reading ApplicationInsights 2.5.1 ...
    Reading Autofac 4.6.2 ...
    Reading Common.Logging 3.4.1 ...
    Reading Tethys.Framework 4.3.1 ...

  Creating Readme_OSS...
    Writing ApplicationInsights 2.5.1 ...
    Writing Autofac 4.6.2 ...
    Writing Common.Logging 3.4.1 ...
    Writing Tethys.Framework 4.3.1 ...

done.
```

#### Create new components and releases on SW360

There are two commands:

`bom createreleases` creates new releases for existing components, but will skip non-existing
components. By default, it requires "ComponentId" information in the SBOM (added by `bom map`
for a package-url match, see discussion there). This is usually a quite safe operation which
can be used in CI pipelines.

`bom createcomponents`, in contrast, will automatically add every unmapped entry in your SBOM to SW360
(only performing very basic checks to not create exact duplicates) -- so this shall only be used after
you manually searched SW360 for the missing components and updated your (mapped) SBOM to not create
any duplicates!

Command:

```sh
capycli bom createreleases -i test_bom_stage_updated.json -o test_bom_stage_updated2.json
-url https://stage.sw360.siemens.com -oa -t eyJhbGciOiJSUzI1NiIsInR5...WA
```

Result:

```sh
CaPyCli - Create new components and releases on SW360

Reading SBOM .\TestData\test_bom_stage_updated.json
Creating items...
  Commander, 3.0.2 already exists
  @babel/code-frame, 7.8.3
    Component @babel/code-frame exists.
      @babel/code-frame, 7.8.3 already exists
    Release has been created, id = 797a6d197e97091e22700c34e4031e41
  TestComponent, 1.0
    Component doesn't exist!
  JSONStream, 1.3.5
    Component JSONStream exists.
    Release has been created, id = 797a6d197e97091e22700c34e4032831
An error occurred during component/release creation!
Exit code = 1
```

#### Create or update a project on SW360

Command:

```sh
capycli project create -name "Toms Test Project" -version "0.0.1"
-i test_bom_stage_updated2.json -source projectinfo.json -url https://stage.sw360.siemens.com
-oa -t eyJhbGci...WA
```

Result:

```sh
CaPyCli - Create or update a project on SW360

Reading SBOM .\TestData\test_bom_stage_updated2.json
Reading project information .\TestData\projectinfo.json
  Searching for project...
  No matching project found!
Creating project ...

Done
```
