<!--
# SPDX-FileCopyrightText: (c) 2018-2026 Siemens
# SPDX-License-Identifier: MIT
-->

# Component Check

The command `bom componentcheck` checks a given SBOM for special components.  
The command  `project componentcheck`. The first one does the same for
an existing SW360 project.

## Why are these commands helpful?

The primary goal of CaPyCLI is to support license compliance. In most cases
license compliance focuses on the third-party software components that are
shipped to customers as part of a product or at least made available for customers.

Obviously this includes only components that are actively used by the application.
Unit test tools like `junit` or `pytest`, linter like `eslint`, mocking frameworks
like `Moq`, etc. are not used by the application. Therefore they should not appear
in a SBOMs or in a SW360 project. These are these **Special components** which
are reported by the `componentcheck` commands.

A second category are Python components that contain additional binary dependencies
in the wheel files. They are reported, because normal license compliance checks
may not show all licenses that apply.

## More Details

Both `componentcheck` commands use a list of special components which is part of
CaPyCLI (see data/component_checks.json). This list has a section for development
dependencies, grouped by package manager, a section for python binary components
and a section for files to get excluded from these checks.

´´´json
{
  "dev_dependencies": {
    "maven": [
      { "namespace": "org.eclipse.jdt", "name": "junit" },
      ...
    ],
    "npm": [
      { "namespace": "", "name": "mocha" },
      ...
    ],
    "pypi": [
      { "namespace": "", "name": "pytest" },
      ...
    ],
    "nuget": [
      { "namespace": "", "name": "NUnit" },
      ...
    ],
    "gem": [ ... ],
    "composer": [ ... ],
    "golang": [ ... ]
  },
  "python_binary_components": [
    { "namespace": "", "name": "numpy" },
    ...
  ],
  "files_to_ignore": []
}
´´´

The current list is only a starting point and we are also aware that there are too
many different projects out there with too many different use cases and components.
Also the list covers only some of the existing software ecosystems.
Therefore it is possible for projects to provide there own lists, either as a local
file (parameter `-lcl` or `--local-checklist`) or as a download URL (parameter
`-lcr` or `--remote-checklist`).

## How is the check done?

For SBOMs the preferred information to determine a component is the package-url.
If it is not available, only the component name is used.

For SW360 project always only the component name is used.
