<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->

# Use Case Overview

For a better understanding where the use cases come from, you may want to have a look
at [Software Clearing Approach Overview](SoftwareClearingApproachOverview.md).

Nearly all commands of CaPyCLI are for developers and not necessarily for software license
compliance experts. The commands should help a development team to determine the bill of
material (SBOM) for their product, find all necessary metadata, upload all necessary
information to SW360 to allow the software license compliance experts to do their work.

There are as well commands to track the status of a project on SW360 and to download
the results to build for example the customer facing license compliance documentation.

## As a developer I want to know the bill of material of my project

CaPyCLI offers a limited direct support to determine the bill of material.
There are the commands

* `getdependencies Nuget`
* `getdependencies Python`
* `getdependencies Javascript`
* `getdependencies MavenPom`
* `getdependencies MavenList`

In general we recommend the [CycloneDX open source tools](https://github.com/CycloneDX) to
determine dependencies.

Whereas the tools are quite good to determine **all** dependencies, they lack any insight
into your project. They do not know what is test code, they do not know about Siemens internal
components. To have a correct bill of material you need to filter out all the information
that is not needed. This can be done with the `bom filter` command.

### Component Granularity

Another issues is the component granularity: assume you are using .NET Core 5.0.
There is an installer that installs all libraries, but you can also pull all the 100+
libraries separately from NuGet. But when looking for the matching source code, you
will only find **one single source code** for all binaries. For this complete source code
we only need one license scan and we only have one clearing report.
==> You should filter your SBOM to have only this single .NET Core 5.x reference.

Example from the Java world: imagine you are using the logging component logback-core.
You can pull the binary from Maven. But there is no source code for logback-core.
The open source project provides only the source for the complete Logback component, see
https://github.com/qos-ch/logback. In the GitHub repository you can also see,
that logback-access and logback-classic are also built from this source code.

## As a developer I want to know which components already exist on SW360

When you have a SBOM then you can run `bom map` to find out which of the components
are available on SW360 or for which versions clearing results already exist.

## As a developer I do not want to search for source code manually

Depending on your software ecosystem and the components you use, we can find most +
source code in an automated fashion:

1. Use CycloneDX to determine the bill of material
2. Run `bom findsources`. This command will update the source url information in the SBOM

## As a developer I want to create a project on SW360 that reflects my SBOM

After running you SBOM through `bom map` **and** manually clearing up/deciding
which components to really use, you can run

* `bom createcomponents` to create all components and releases
* `bom create project` to create you project and link all releases

## As a developer I want to know the status of my project

The command `project show` lists all components of the project and the project mainline state.

## As a developer I want to download all software license compliance results

The command `project GetLicenseInfo` downloads the CLI files for the components of your project.

**Note:** at the moment only the first CLI file found is downloaded per component.

## As a developer I want to build the Readme_OSS for my project

Once you have downloaded and CLI file you can run the command `project CreateReadme`
to generate a Readme_OSS in HTML format.

**Important:** The generated Readme_OSS will contain **all** license and **all** copyrights
available in the CLI files. In most cases this is not exactly the information you need for
your project. Please have a clearing expert review the generate Readme_OSS to see if any
changes are required.
