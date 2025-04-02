<!--
# SPDX-FileCopyrightText: (c) 2024 Siemens
# SPDX-License-Identifier: MIT
-->

# CaPyCli - SBOM Filtering

Why do we need a filter functionality for SBOMs?  
Well, not all SBOMs are really perfect, i.e. they may not contain
what we expected - sometimes there are too many components, sometimes
there are too few components.

## Table of Contents

[Example 1: Remove a specific component](#example-1-remove-a-specific-component)
[Example 2: Add a component](#example-2-add-a-component)
[Filter Specification](#filter-specification)

We start first with some examples. The full specification is the last section.

## Example 1: Remove a specific component

Imagine you have created a very small Javascript application that just compares  
two text files and shows the difference. It took only two OSS components,  
`commander, 3.0.2` for the command line handling and `diff_match_patch, 0.1.1`  
to create the diff.

When you create an SBOM using `cyclonedx-npm`, then the resulting SBOM contains
**THREE** components and not only two:

* commander, 3.0.2 - **expected**
* diff_match_patch, 0.1.1 - **expected**
* JavaScript_diff, 0.0.1 - **not expected, because this is our application itself**

We can use the CaPyCLI filter functionality to remove `JavaScript_diff, 0.0.1`.

### Example 1: Create Filter File

Create the file `filter.json`:

```code
{
  "Components": [
    {
      "component": {
        "Name": "JavaScript_diff",
        "Version": "0.0.1"
      },
      "Mode": "remove"
    }
  ]
}
```

### Example 1: Run Filter Command

Run the following CyPyCLI command:

```shell
capycli bom filter -i ./bom_original.json -o ./bom_filtered.json -filterfile ./filter.json -v
```

Console output:

```shell
CaPyCli, 2.6.0.dev1 - Apply a filter file to a SBOM

Loading SBOM file ./bom_original.json
  3 components read from SBOM
Applying filter file ./filter.json
  Got 1 filter entries
  Total 1 filter entries
  Removing JavaScript_diff, 0.0.1

Writing new SBOM to ./bom_filtered.json
  2 components written to SBOM file
```

The result is the SBOM `bom_filtered.json` which contains exactly the two
components we were looking for.

## Example 2: Add a component

Imagine you have created a very small Javat application that just compares  
two text files and shows the difference. It took only few OSS components.

When you create an SBOM using `capycli GetDependencies MavenPom`, then the
resulting SBOM contains all direct Java dependencies, but one thing is
missing - **the Java runtime itself**.

This is based on the tooling as it focuses on the information that is
available **inside the ecosystem.** But if you like to have an SBOM that
contains everything that needs to get shipped (or needs to be available at
the customer site), then you also need the Java runtime.

We can use the CaPyCLI filter functionality to add a Java runtime.

### Example 2: Create Filter File

Create the file `filter.json`:

```code
{
  "Components": [
    {
      "component": {
        "Name": "OpenJDK",
        "Version": "22.0.26"
      },
      "Mode": "add"
    }
  ]
}
```

### Example 2: Run Filter Command

Run the following CyPyCLI command:

```shell
capycli bom filter -i ./bom_original.json -o ./bom_filtered.json -filterfile ./filter.json -v
```

Console output:

```shell
CaPyCli, 2.6.0.dev1 - Apply a filter file to a SBOM

Loading SBOM file ./bom_original.json
  3 components read from SBOM
Applying filter file ./filter.json
  Got 1 filter entries
  Total 1 filter entries
  Added OpenJDK, 22.0.26

Writing new SBOM to ./bom_filtered.json
  4 components written to SBOM file
```

The result is the SBOM `bom_filtered.json` which contains exactly the
components we were looking for.

## Filter Specification

A filter is a JSON file. It has two sections:

* an optional `Include` section to include additional filter files
* a `Components` section that defines which component should be modified.

The `Components` section is a JSON array of objects that have
a mandatory `component` (object) property, a mandatory `Mode` property
(either `add` or `remove`) and an optional `comment` property.

When a component is to be *removed*, it can be identified by its `package-url`
(recommended) or by its `Name` and `Version`.

When a component is to be *added*, the following component properties
can be used:

* `Name`
* `Version`
* `Language`
* `SourceFileUrl`
* `SourceFile`
* `BinaryFile`
* `Sw360Id`

The expected filter file format is

```code
    {
        "Include": [
            "optional-Sub-Filter_to_include.json"
        ],
        "Components": [
            {
                "comment": "optional comment",
                "component": {
                    "Name": "a component name"
                },
                "Mode": "remove"
            },
            {
                "component": {
                    "Name": "another component name",
                    "Version" : "component version"
                },
                "Mode": "add"
            }
        ]
    }
```
