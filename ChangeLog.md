<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->

# CaPyCli - Clearing Automation Python Command Line Tool for SW360

## NEXT

* Be more resilient about missing metadata in CycloneDX SBOMs.
* The `-o` parameter of the command `project GetLicenseInfo` is now optional.
  But you still need this output when you want to create a Readme.
* `project createbom` add purls, source and repository url from SW360 if available.
  If multiple purls are found, a warning is printed asking user to manually edit SBOM.
* `project createbom` add SW360 attachment info as external references to SBOM
  (currently supported: source, binary, CLI, report).
* `project createbom` adds SW360 project name, version and description to SBOM.

## 2.0.0 (2023-06-02)

* Have an updated granularity list.
* Re-enable support for Python 3.8 and 3.9.
* A list of frequently asked questions has been added.
* `getdependencies python` now also accepts a Poetry lock file (must be `poetry.lock`) as input.
  Development dependencies are automatically excluded.
* [Code of conduct](CODE_OF_CONDUCT.md) added.
* Warnings about multiple purls entries when running `bom map` are now only shown if `-v` has been specified.
* breaking change
  * `bom map` will report matches by name, but different version **only** if `-all` has been specified.
    The original idea of CaPyCLI was to report as many potential matches as possible and to let the user
    decide which match to take by editing the SBOM. But it seems that many users did not read the documentation
    and the expectations were different. Therefore the default behavior has been changed.
    The original behavior of versions prior to 2.x can be enabled via the `-all` switch.

## 2.0.0.dev (2023-05-19)

* breaking changes
  * new command `bom convert` to import and export SBOM in mutiple formats.
    This new command replaces `bom fromCSV`, `bom FromFlatFist`, `bom FromSbom`,
    `bom ToHtml` and `bom ToSbom`.
  * `bom sort` is discontinued, CycloneDX SBOMs are always sorted by component name.
  * The option `-source` of `GetDependencies python` is discontinued, please use
    `bom downloadsources` instead.
  * `project show` writes the output file only in plain JSON and not CycloneDX.
  * `project CreateReadme` requires new entries in readme_oss_config.json to be independent
    of the name Siemens
    * `CompanyName`
    * `CompanyAddressN`, N = 1..4
  * `bom map` now uses alphanumeric identifier for mapping instead of integer values:
    * INVALID: `0-invalid` instead of 0
    * FULL_MATCH_BY_ID: `1-full-match-by-id` instead of 1
    * FULL_MATCH_BY_HASH: `2-full-match-by-hash` instead of 2
    * FULL_MATCH_BY_NAME_AND_VERSION: `3-full-match-by-name-and-version` instead of 3
    * MATCH_BY_FILENAME: `4-good-match-by-filename` instead of 4
    * MATCH_BY_NAME: `5-candidate-match-by-name` instead of 5
    * SIMILAR_COMPONENT_FOUND: `6-candidate-match-similar-component` instead of 6
    * NO_MATCH: `9-no-match` instead of 100
  * `bom map` now uses alphanumeric identifier for map modes (`-m`) instead of integer values:
    * `all` instead of 0
    * `found` instead of 1
    * `notfound` instead of 2
  * dropped support for option `-stage`. The SW360 server instance can get specified via the `-url` parameter.
  * The hard coded address https://sw360.siemens.com has been removed.
    CaPyCLI reads the SW360 server address either from the environment variable `SW360ServerUrl` or
    via the `-url` parameter.
  * CaPyCLI supports an optional config file `.capycli.cfg`. Settings defined in the config file
    supersede settings in environment variables. Command line parameters supersede config file settings.
* The cache functionality of `bom map` also supports the staging system.
* `project GetLicenseInfo` can take over data from existing Readme_OSS config files.

## 1.9.1 (2023-03-23)

* Purl cache will only retrieve package URLs from SW360 with the types used in
  BOM to reduce the number of warnings for inconsistent SW360 entries.
* use CycloneDX BOM syntax from https://sbom.siemens.io/v2/format.html for
  source urls ("comment": "source archive (download location)" in `externalReferences`)
* support CycloneDX externalReferences/hashes for SHA-1 hash
* All commands have now proper result/exit codes, see [Exit Codes](Exit_Codes.md).
* `project GetLicenseInfo` can now add **all** available CLI files to the readme configuration file
  if the `-all` option is being used. A warning will be displayed if there are multiple CLI
  files for the same component.
  `project CreateReadme` will put all contents of all CLI files in the Readme_OSS, but will also
  display a warning when there are multiple CLI files for the same component.
* The use of "id" to identify a release has been deprecated, we now only use "Sw360id".
* `bom check` and `bom checkitemstatus` now process also BOM item without Sw360id. In this case
  they will search SW360 by name and version ... which takes much more time.

## 1.9.0 (2023-01-09)

* Drop support for Python 3.6 and 3.7 due to dependency updates and the new
  OSS version of cli, called cli-support.
* use sw360, version 1.2.1 with minimal logging support.
* Have direct help support for `project licenses`, `project createreadme`,
  `project createbom`, and `project GetLicenseInfo`.

## 1.8.3 (2022-11-11)

* `bom map` is now more resilient about errors during the mapping of a single BOM item.
* `bom map` has a new parameter `mode`. If mode is not set, then there is the default mapping.
  If `mode` = 1, then the resulting BOM contains only components where a full match was found.
  If `mode` = 2, then the resulting BOM contains only components where no match was found.
* `getdependencies python` and `project prerequisites` now support CycloneDX SBOM.
* `bom filter` `add` command can now add properties to existing bom items.
* `bom downloadsources` handles quotes in filenames returned by content-disposition.
* `bom downloadsources` can now write an updated BOM including SHA1 hashes.
* In CycloneDX SBOMs, the URL to source files will now be stored and read to/from
  `externalReferences` of type `distribution` (with special comment "source URL") in
  addition to our custom `source-file-url` property.
* Fix command `project show` which cause an exception if some of the mandatory data is missing
* `--dbx` (Debian relaxed version handling) in `bom create...` improved: First, it will check
  for exact matches now. When falling back to relaxed matching, Debian epoch strings are
  ignored, while Debian revisions are always considered. Output BOM will have SW360 versions.
* `bom create*` will set package-urls for existing and new components
* Key error issue fixed in maven_pom.py.
* All commands show now the version number, i.e. something like `CaPyCli, 1.8.3`.

## 1.8.2 (2022-07-13)

* Fix in CycloneDX reading of JavaScript or Java component that have a `group` property.
* New command `project ecc` to show the project export control details.
* Fix: when `bom granularity` reads a BOM in CycloneDX format, it now also writes the BOM in
  CycloneDX format.

## 1.8.1 (2022-07-01)

* Fixed bug in `getdependencies javascript` when not all meta information for a package could get retrieved.
* `bom downloadsources` now supports also option ```-cx``` to support the CycloneDX SBOM format.
* CycloneDX JSON BOMs are expected in UTF-8 encoding.
* `bom map` has now a much faster way to create/update the cache. Due to the new SW360 REST API
endpoint to get all releases with one call it now takes only 1.3 minutes.
* `project vulnerabilities` is working again. It seems that there was a breaking change in the REST API
  answer.

## 1.8.0 (2022-04-07)

* Fix bug in `bom findsources` when using CycloneDX bom files.
* Improved help support
  * When no command has been specified, the global help will be shown.
  * When no sub-command has been specified, the respective command help will be shown.
* `project vulnerabilities` uses only the information from SW360 to display security vulnerabilities
   and can exit with exit code 1 when a not yet handled security vulnerability of a certain
   minimum priority has been found.

## 1.7.0 (2022-03-25)

* `project show` now also displays the component clearing state.
* `bom filter` allows to include additional filter lists. This simplifies filtering
  for large number of BOM entries and many items to get filtered.
* `bom create*` will now ignore rejected attachments in SW360.
  So if an invalid attachment is rejected in SW360, it will upload the fixed sources.
* `project update` will not overwrite links to other projects any more
* A couple of crashes have been fixed in `bom map`, `bom filter` and `project create`.
* several fixes for purl cache handling.

## 1.6.0 (2022-02-08)

* **License changed to MIT!**
* `bom map` handles now also multiple package-urls per release correctly.
* new command `project update` which will *add* new releases instead of replacing existing links.
* `project prerequisites` now checks if all BOM entries are in SW360 project.
* BOM mapping documented.
* `bom CheckItemStatus` updated:
  * the new default is that only the releases in the BOM are shown. Only when the flag `-all` is specified,
    all versions of the component are checked.
  * new option `-cx` to support the CycloneDX SBOM format.
  * Have improved help support.
* New command `bom findsources` to find source code for existing BOMs.
* `bom filter` supports removal of entries by `RepositoryId`. This is sometimes required
  when a (CycloneDX) BOM contains several items with the same name.
* `getdependencies javascript` creates a BOM item with the name `Homepage`. This is not the
  intended name, it has to be `ProjectSite`. The code for dependency detection and component
  creation has been updated. For compatibility both names are support, but `Homepage`
  is marked as deprecated.
* `bom findsources` is more fail save and allows to specify GitHub credentials.

## 1.5.0 (2021-12-20)

* New parameter `-package-source` to specify a custom package manager.
  The parameter is very helpfull if your are in an environment where you cannot access
  the internet, for example when running CI/CD on code.siemens.com.
  Package metadata can get retrieved for example from BT-Artifactory:
  * NPM: https://devops.bt.siemens.com/artifactory/api/npm/npm-all/
* Fix: NOT_README_OSS tags are now properly handled during Readme_OSS generation.
* The granularity check reset all release information which are not correct anymore after merging
  them by granularity check.
* When downloading files in `bom createcomponents`, filenames are now updated according to
  HTTP `content-disposition`.
* `bom diff` can now write lists of different and of identical BOM items.
* `bom map` has some improvements in package-url handling.
* `getdependencies javascript` has an improved method to determine source files.
* `getdependencies MavenList` has improved parsing of Maven output.
* `project create` can now use all data in projectinfo.json that conforms with the REST API
  specification. It is now for example also possible to add attachemnt during project creation.
* New option ```-cx``` to support the CycloneDX SBOM format for the commands
  * `bom diff`
* Unit tests for `bom diff` added.
* Improved help support:
  * When `-h` is specified for a main command, a help on all respective subcommands.
    Available for `bom`, `moverview`, `mapping`, `project`, `getdependencies`.
  * When `-h` is specified for a sub-command, then a specific help for this sub-command is shown.
    Available for `show bom`, `bom filter`, `bom diff`, `bom merge`, `bom check`, `bom granularity`,
    `bom fromsbom`, `bom map`, `bom createcomponents`, `bom downloadsources`,
    `mapping toxlsx`, `mapping tohtml`, `moverview toxlsx`, `moverview tohtml`,
    `getdependencies python`, `getdependencies javascript`, `getdependencies nuget`,
    `getdependencies mavenpom`, `getdependencies mavenlist`.

## Pre-release 1.5.0b1 (2021-12-03)

* `bom filter` now supports trailing wildcards.
* Improved CycloneDX handling (schema 1.3) for commands `bom fromsbom` and `bom tosbom`.
* New option ```-cx``` to support the CycloneDX SBOM format for the commands
  * `bom show`
  * `bom filter`
  * `bom map`
  * `bom check`
  * `bom createcomponents`
  * `project create`
  * `bom granularity`

## 1.4.1 (2021-12-03)

* Fix wrong project id assignment in `project show`.

## 1.4 (2021-12-03)

* `bom create` supports additional BOM fields `SourceFileType` and `SourceFileComment`
* `bom create` now supports updating of existing releases - source URL and
  external ID will be added if not set already. Source file will be uploaded if
  the existing release has no source attachments - otherwise `capycli` will
  warn if existing upload doesn't match BOM. So `bom create` can be interrupted
  and resumed at any time or just ran to verify existing releases.
* `getdependencies javascript` now creates package-urls and no longer npm-ids.
* `getdependencies nuget` now creates package-urls and no longer nuget-ids.

## 1.3 (2021-11-15)

* `bom create` with `--dbx` option will re-use existing SW360 releases with
  "similar" Debian versions. It will ignore epoch prefix ("2:") and ".debian"
  suffix, so BOM entry "2:5.2.1-1.debian" will match SW360 release "5.2.1-1".
* `bom create` only downloads missing sources if ```--download``` is specified
* `bom create` now respects filename given in "SourceFile" also when "SourceFileUrl" is given
* `getdependencies python` now uses the common ```-source``` option to specify the folder for
  downloading sources instead of the special ```--download_sources``` option
* `getdependencies mavenlist` allows now to specify a Maven dependency file using the ```-i``` option.
  This file is then converted to a BOM.

## 1.2 (2021-10-28)

* `project createbom` to create a CycloneDX SBOM file for an existing SW360 project.

## 1.1.1 (2021-09-28)

* improve error output for `project create` and `bom CreateComponents`.
* fix: adapt moderators handling for `project create`.
* fix temp folder handling and attachment upload for `bom CreateComponents`.

## 1.1.0 (2021-09-24)

* `bom fromsbom` supports also JSON CycloneDX SBOMs.
* `bom fromsbom` extracts also `ProjectSite` and `RepositoryUrl` from SBOMs.
* missing dependency chardet added.

## 1.0.0 (2021-09-21)

* improved JavaScript metadata search and evaluation.
* new command `bom granularity` to check a bill of material for potential component
  granularity issues.
* `getdependencies nuget` now also handles Visual Studio solution files.
* `getdependencies javascript` is more flexible about missing information.
* new feature `bom diff` to compare two bills of material.
* new feature `bom merge` to merge two bills of material.
* the exit code is only displayed when the `-ex` option has been specified.

## 0.9.9 (2021-06-22)

* `project prerequisites`: If a BOM with "SourceFileHash" entries is provided
  as input, verify SHA1s of sources. It also checks that there's exactly one
  source file per release.
* new command `bom createReleases` to limit automation to creation of new releases
  in components identified via package-urls (see [example.md](example.md))
* `bom map`: full support for searching components and releases by package-url (purl)
  in ```--nocache``` as well as in default mode
* `bom map`: leave original item im BOM if no good release match was found,
  and include "ComponentId" if we  know if for sure (e.g. match by purl)

## 0.9.8.1 (2020-11-20)

* due to a breaking change in the SW360 REST API:
  ```downloadurl``` has been replaced by ```sourceCodeDownloadurl```

## 0.9.8 (2020-11-09)

* check_prerequisites.py: better handling of missing keys

## 0.9.7 (2020-11-09)

* fixed bug that crashed capycli if ```-old-version``` param was missing

## 0.9.6 (2020-11-03)

* new switch ```-old-version``` to update an existing project to a new version instead of
  creating a new project (thanks to Bogdan Victor Serbanescu).

## 0.9.5 (2020-10-09)

* Added extra validation (name equality) when choosing a matching component
  (thanks to Bogdan Victor Serbanescu).

## 0.9.4 (2020-09-21)

* Fix: project show status: check that a release has "_embedded" data.
* version 0.9.4 released.

## 0.9.3 (2020-06-04)

* new command `bom downloadsources` to download source files
  from the URL specified in the BOM.
* all errors result in exit code = 1.
* new option `-source` for command `bom createcomponents` to specify
  a folder where to find/store source code files.
* `bom createcomponents`: source code files will onl get downloaded if they
  do not yet exist locally.
* fix: correct handling of components without releases.

## 0.9.2 (2020-05-22)

* automatic upload of source files/urls as attachments
* determine source code URL for JavaScript component from package-lock.json
* version 0.9.2 released

## 0.9.1 (2020-05-13)

* creation of components fixed
* version 0.9.1 released

## 0.9.0 (2020-05-05)

* new structure: there is only one script: CaPyCli
* version 0.9.0 released, binaries are available on BT-Artifactory

## 2019-05-29

* Improved error handling in sw360_api.py:
* Base class for scripts added

## 2019-05-28

* Introduced pipenv (Pipfile, Pipfile.lock)
* Replaced ansi by colorama for better compatibility
