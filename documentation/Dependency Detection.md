<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->

# Dependency Detection

This is a collection of information about determining the dependencies of a projects,
or determining the SBOM, the bill of material for a project.

## Nuget/C#/.Net

### Information available on NuGet

All information shown on Nuget (https://www.nuget.org/) is pulled from
the nuget packages itself - no additional information is added manually.  
Examples:

* [Tethys.Logging 1.6.1](https://www.nuget.org/packages/Tethys.Logging/1.6.1)
* [AbrarJahin.DiffMatchPatch 0.1.0](https://www.nuget.org/packages/AbrarJahin.DiffMatchPatch/0.1.0)

### Information in the NUSPEC file

* Name (mandatory)
* Version (mandatory)
* Description (mandatory)
* Authors (mandatory)
* Website (`projectUrl`, optional)
* Version Control System (`repository`, optional)
* License (`license` or `licenseUrl` (deprecated), optional)
* Copyright (`copyright`, optional)
* Release Notes (`releaseNotes`, optional)
* Title = user  friendly name of the package (`title`, optional)
* Dependencies (optional)

There is no reliable information about the source code. A heuristic would be to look
for the version control system or website. If it is GitHub, then try to guess the
source code file, see GitHub section.

### CaPyCLI v1.0 / NUSPEC

CaPyCLI 1.0 reads the `packages.config`, `.csproj` or `.sln` file and extracts name
and version. From this information the package-url is created.

There is no support to download the source code.

### CycloneDX

CycloneDX (https://github.com/CycloneDX/cyclonedx-dotnet) searches recursively all Visual Studio
solution or project files for package references. The meta data of the packages is retrieved from
the nuspec file on the NuGet packages. The NuGet packages are found in the global NuGet cache
folder.

### CC Automation (DI)

CC Automation needs access to all build results of the project, especially to
the `deps.json` files and the `packages` folder. The tool allows to provide
a list of packages that should get ignored.

(some magic)

CC Automation uses the NuGet API to retrieve meta data about the packages.
This meta information also can contain repository meta data like the
repository URL and the commit id. Only if this information is available,
the source code URL can then be created like this:
`
https://github.com/{WebUtility.UrlEncode(owner)}/{WebUtility.UrlEncode(name)}/archive/{commitSha}.tar.gz
`

This method is clever, but does not work for Microsoft packages.

---

## JavaScript

### Information available on NPM / in the package.json file

* Name
* Version
* Description (optional?)
* Homepage (optional)
* Repository (optional)
* Author (optional?)
* License (optional)
* Dependencies (optional)

Examples:

* [@angular/cli 13.0.4](https://www.npmjs.com/package/@angular/cli)

### CaPyCLI v1.0 / JavaScript

CaPyCLI 1.0 reads the `packages.json` or better `package-lock.json` file and extracts name
and version. From this information the package-url is created.
If a `resolved` entry is found, then it is used as URL of the binary.

The URL for meta information is guessed as

```code
url = "https://registry.npmjs.org/" + Name + Version
```

If the URL exists, then the following properties may get extracted:

* Homepage
* SourceUrl
* Description
* BinaryFileHash

### CycloneDX / JavaScript

*...detailed analysis pending...*

CycloneDX (https://github.com/CycloneDX/cyclonedx-node-module) uses the package
`read-installed` to determine all packages. This list in then transferred to a CycloneDX
bill of material.

Available information:

* Name
* Version
* Description
* License
* package-url
* Homepage
* Repository

---

## Python

### Information available on PyPi

All information shown on PyPi (https://pypi.org/) is pulled from
the pypi packages itself - no additional information is added manually.  
Examples:

* [sw360 1.1.0](https://pypi.org/project/sw360/)
* [packageurl-python 0.9.6](https://pypi.org/project/packageurl-python/)

Available Information:

* Name
* Version
* Homepage
* Repository

### CaPyCLI v1.0 / Python

CaPyCLI v1.0 can either parse a `requirements.txt` file or call `pip3 list --format json`.
For a `requirements.txt` file we only get the component name and version and create the
package-url out of it.  
With internet access we can guess the PyPi URL:

```code
url = https://pypi.org/pypi/ + name + / + version + /json
```

If the URL exists, then the following properties may get extracted:

* ProjectSite
* DeclaredLicense
* Description
* BinaryFile
* BinaryFileUrl
* SourceFile
* SourceFileUrl

### CycloneDX / Python

*...detailed analysis pending...*

---

## Java

### Information available on Maven

*...detailed analysis pending...*

### CaPyCLI v1.0 / Java

*...detailed analysis pending...*

### CycloneDX / Java

*...detailed analysis pending...*

---

## Other Languages / Software Eco Systems

People are working on support for Debian packages and Ruby, but it may still take some time...

---

## Guessing the Source Code Location

Nearly no component management system provides reliable information of the source code.
From the development point this is only optional - an application only requires the binary.
Information on the sourec code repository or website if often available. What we can do, is
to guess the source code download address from the website.

### GitHub

Assume we have the component `Tethys.Logging, 1.6.1` and the website address
`https://github.com/tngraf/Tethys.Logging`. The we can **guess** the source code download
address `https://github.com/tngraf/Tethys.Logging/archive/refs/tags/v1.6.1.zip`.

If the URL exists, then we are fine; otherwise a human have to look up the source code.

## FAQ

* **Q:** Why does CaPyCLI provided only limited support for dependency detection?  
  **A:** At beginning most people where happy with a very simple automation that
  just created components and releases on SW360. All other meta has been entered manually.
  At the end all is inner source - if you need something, fell free to implement it ;-)
  Please keep also in mind that getting more meta information often requires to pull
  additional information from the internet - which is not available on all build machines.
