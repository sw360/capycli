<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->>

# Software Clearing Approach Overview

## Smart Infrastructure - Building Products (SI BP)

SI BP has more than 1000 software developers but less than 15 persons doing software
license compliance. Our management emphasized that these software license compliance
experts shall focus on their area of expertise - software license compliance. It is their job
to ensure that we ship products that fulfill all license obligations - it is **not**
their job

* to determine bills of material
* to find the source code of open source components
* to verify whether this is the correct source code
* to find additional meta data on a software components
* to take care of security vulnerabilities
* to take care of export control
* to take care of intellectual property rights or patents

### Basic Rules for using Third Party Software

#### Rules for Projects

* The development team is responsible for the selection of third party software components
  **and for the fulfillment of all prerequisites** mentioned below
* The development team shall be aware of **the total effort/cost** implied by selecting a
  specific  component (size and future maintenance vs functionality used)
* A complete list of all third party software components used by the product needs to be
  maintained (every "product release version" as new project in SW360)
* The SI Software Clearing Team is supporting the clearing activities (consulting, best
  practice sharing, source scanning, generation of clearing report, ...) by confirming that our
  organization is able to follow the obligations of a component
* Fulfilling all license, patent and export control obligations is in the responsibility of
  the project team or agile release train
* The project team or agile release train has **to plan** all software clearing related
  activities, including the product clearing as part of the development cycle
* A product feature is only done, if also all required third party software components have
  been cleared (Definition of Done)
* A product or solution can only be released or shipped when product clearing has been
  successfully passed (Definition of Done)

#### Prerequisites for using a third party software are

* you have checked on SW360 whether the component is already listed
* one goal shall be **to reuse components**, so you should have a solid reason to use a new one
* you know where the component comes from (community, software vendor) and in case of OSS if
  there is an active community
* you know the license, at least the main license - see also OSS Licenses Explained (add. tool
  support is currently under investigation)
* you know basic functionality
* you have checked the component for any patents or other potential intellectual property
  issues
* you have check whether there are any security vulnerabilities
* you have checked for any dependencies
* updates are also a conscious decision (no automatic updates, limited exceptions are possible
  depending on component and semantic versioning concept)!
* in case of an updates:

  * you know what has changed (functionality and base license)
  * checking the dependencies about what is really new can speed up delta clearing
      significantly
* you had an introduction to software clearing, SW360 and how to upload sources and binaries

If these prerequisites have been fulfilled you are ready to apply for the component on SW360

**Hint:** Software clearing @ SI is a continuous process, early upload of new components avoids product
release delays

### Total Cost of Ownership

From the management point of view it does not make a real difference which person of which team
handles a specific task. It is about the total effort, the total costs, that sum up when creating a
product. If one team decides to act in a way that another team has to do more work,
then this contradicts the goal of minimizing the total cost of ownership.

Examples:

* using always the latest version of a third party software component might be nice for the
  development team, but can significantly increase the software clearing effort. But when
  software clearing is not done, the product cannot get released.
* the developers need to take a look on SW360 to find out which components and which versions
  of the components have already been cleared. With this information they can select components
  that do not require additional clearing effort and save time and money.

### SI BP Software Clearing Approach in a Nutshell

* Developers are encouraged to apply for components as early as possible on SW360.
  The more early there is a request, the more early a component is cleared!

  * Because of this successive approach there is never a big bang like a request
    to clear 100+ components on short notice.
* Developers have to create new components and releases on SW360. They decided which
  components to use in their product and they are responsible to provide all necessary
  information on SW360. When information is missing, software clearing cannot start
  and the project get delayed.
* Developers may use automation to update all the information on SW360, but at the end
  they are always responsible for the completeness and correctness.
* SI BP developers learned that introducing a new third party software component costs
  some effort:

  * check suitability for a certain purpose
  * check maturity of the component
  * check community reliability, secure development, and vulnerability management
  * check patent situation
  * check for potential security vulnerabilities
  * check for export control information
  * check the license
  * find the source code, build the component
  * provide all necessary information on SW360
  Only the last two tasks are related to software clearing and manually creating a new release
  on SW360 takes less than 5 minutes...
* Software component clearing starts as soon as the software clearing team is aware of the
  new component.
* Developers can track (automatically) the clearing state of the components of their project
  on SW360. For many of them this is a continuous integration step.
* Once all components are cleared, the development team can apply for product clearing.
  The resulting artifacts of product clearing are a product clearing report and a Readme_OSS
  in HTML, Word or plain text format.
* Development teams may use the information on SW360 to create a Readme_OSS - for example as
  part of the CI pipeline, but the final Readme_OSS needs to get reviewed by a clearing expert.
* The SI BP quality team tracks that all components got cleared and that a product clearing
  report is available. Only if all the prerequisites are fulfilled a product release is possible.

## General Topics

### Why should developers upload source code to SW360

Sometimes there are complaints by the development team that it costs so much time to find the
source code for the open source components and to upload it to SW360.

Well, there seems to be a general misunderstanding: it is called **open source** software,
i.e. the publicly available source code is the only truth. Binaries might be available, but in
many cases the original open source community only provides the source code.

* Only the developers know what they exactly use.
* Only the developers can use the source code to build the binaries and this is
  the only way to verify whether this is really the correct and complete source code.
* Many open source licenses (CDDL, GPL, LGPL, MPL) require that Siemens is able to provide
  customers with the source code
* Licenses like AGPL, GPL, and LGPL require that we ship exactly the source code that has been
  used to built the binaries, including all build files. There have been a number of cases
  where companies got sued because they were not able to provided this very source code.
  So for all components under these licenses **it is mandatory for the developers to verify in
  detail that they have the correct source code.**
* The developers also need to be able to answer all questions by the software clearing team
   regarding certain files or the usage of certain files.

**Software clearing experts do not need to be developers. They cannot decide on the correctness
of the source code. They also do not need to know in detail how to find the source code for a
specific version of a component in a source code repository. All this is a developer task!**

### What is the correct source code

As already mentioned before, we are looking for the original source code from the open source
community. They are the copyright holders, only they decide about the full extent of their
source code. **Taking source code from another location is a risk and has to be avoided!**

General repositories like Maven or Siemens internal repositories like any Artifactory instance
are no allowed locations to take source code from!

#### Why should a Maven Source Artifact not get used for Software Clearing?

* A Maven Source Artifact is considered for debugging, i.e. to allow development environments
  to provide information about the sources.
* There is no definitive definition what must be contained in Maven Source Artifact, so in
  most cases it only contains plain Java files.
* Licensing information like LICENSE.txt, NOTICE.txt or other information like Readme.md is
  missing in most cases … and so there is no guarantee that we would find all licensing information.
* Normally you also cannot build the binary from these sources, i.e. a Maven Source Artifact
  is clearly not the source code that has to be provided for licenses like GPL, LGPL, EPL, MPL, etc.

**There is a certain probability, that using a Maven Source Artifact for software clearing my lead
to a licensing infringement!**

Example: checker-qual-2.8.1

This is an example to show why source code from maven is not really useable for Siemens license scanning.

* The source file checker-qual-2.8.1-sources.jar is from maven
  (https://mvnrepository.com/artifact/org.checkerframework/checker-qual/2.8.1).
* The source file gson-gson-parent-2.8.2.zip is from the real authors at
  https://github.com/typetools/checker-framework/releases.

Manual evaluation:

* While the pure source files are binary identical, all non-code files are missing in the
  maven repository. This is especially critical, because the file LICENSE is only available
  in the non-Maven repository! The Maven source artifact does not contain any licensing information!
