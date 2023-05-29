# CaPyCLI - Frequently Asked Questions

## What is the difference between CreateReleases and CreateComponents?

SW360 knows components and releases. Releases are specific versions of a component.
Some people take more care when choosing component names than others. Assume the
component `spring-boot` already exists on your SW360 instance. Then it would not
be the best idea when someone adds additional components `Spring Boot`, `spring_boot`
or `Apache SpringFramework Boot`.  
`CreateReleases` allows only to create new releases of an existing component.
`CreateComponents` will also create missing components.
**So be careful when using `CreateComponents`.**

## Why are there sometimes multiple entries of a components in the SBOM after mapping?

CaPyCLI has different modes for mapping an existing SBOM to the data available on SW360.
One mode list all available releases of a component *if the matching release does not
exist on SW360*.

Example:
Assume you are looking for the release `Tethys.Logging, 1.4.3`.
When `CaPyCLI bom map` displays

```shell
Match by name, Tethys.Logging, 1.4.3 => Tethys.Logging, 1.6.1 (and 5 others)
```

then the resulting SBOM will contain

* `Tethys.Logging, 1.4.3` with the mapping code `9-no-match`.
* `Tethys.Logging, 1.6.1` with the mapping code `5-candidate-match-by-name`
* 5 more releases of `Tethys.Logging` with the mapping code `5-candidate-match-by-name`

**=> Depending on the mapping result a review/editing of the resulting SBOM is required!**

## What is 'Granularity'?

In a software project you use the libraries you need. You pull them from the packet manager
of your software ecosystem (NuGet, Maven, NPM, PyPi, etc.). For license compliance analysis
you need the source code of these binaries. Often many binaries are built out of the same
source code. `Granularity` is about have the appropriate data on SW360. At Siemens we prefer
to the the source code granularity, i.e. we have components like `Angular` or `spring-boot`
and not separate components for `@angular/animations/browser`, `@angular/compiler` or
`spring-boot-actuator-autoconfigure` and `spring-boot-starter-aop`.
