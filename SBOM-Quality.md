# SBOM Quality

When you use CaPyCLI to create an SBOM and then run an SBOM quality checker like
[sbomqs](https://github.com/interlynk-io/sbomqs) on this newly created SBOM, the tool will report
not the best quality.

* There are no authors
* There are no suppliers
* There is no SBOM lifecycle
* There are no checksums reported
* There is no signature
* There seem to be no dependencies declared
* There is no completeness declared
* There is no primary component
* There is no source code for components
* There are no suppliers for the components

Well, most of this is correct. But like always when you create SBOMs
and validate SBOMs it is about the **use case.**

CaPyCLI is **not designed** to create an SBOM that can be used for NTIA, OpenChain Telco,
or Germany BSI use cases. CaPyCLI creates SBOMs for license compliance purposes. They
are intended on the **input side**. They need to get checked by the developers of a product
for completeness. Information about authors and suppliers needs to get added.  
Information about licenses, suppliers or source code of components can only get provided,
when this information is available in the respective software eco-system.
