<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->

# Contributing to CaPyCLI

We **welcome** contributions in several forms, e.g.

* Improve user documenting

* Testing
  * e.g. by using the SW360 base library in different scenarios
  * Write unit tests and learn how the code works

* Working on [issues](https://github.com/sw360/capycli/issues)
  * Fix a bug
  * Add a new feature

* etc.

## Reporting Bugs

CaPyCLI uses GitHub's issue tracker. All bugs and enhancements should be
entered so that we don't lose track of them, can prioritize, assign, and so code
fixes can refer to the bug number in its check-in comments.

The issue usually contains much more detail (including test cases) than can be
reasonably put in check-in comments, so being able to correlate the two is
important.

Consider the usual best practice for writing issues, among them:

* More verbosity rather than one liners
* Screenshots are a great help
* Providing example files (in case for example scanning crashes)
* Please determine the version, better the commit id
* Details on operating system you are using

## New Features

You can request a new feature by submitting an [issue](https://github.com/sw360/capycli/issues/new).

If you would like to implement a new feature, please consider the scope of the new feature:

* *Large feature*: first submit an issue and communicate your proposal so that the community can
   review and provide feedback. Getting early feedback will help ensure your implementation work is
   accepted by the community. This will also allow us to better coordinate our efforts and minimize
   duplicated effort.
* *Small feature*: can be implemented and directly submitted as a Merge Request.

## Setup

This project uses [poetry]. Have it installed and setup first.

To install dev-dependencies and tools:

```shell
poetry install
```

## Coding Conventions and Style

We use [Flake8](https://flake8.pycqa.org/en/latest/) to check the code style.

```shell
poetry run flake8
```

If Flake8 fails, the build fails ... and we probably will not merge your code...

## Testing

```shell
poetry run pytest
```

We should always have unit test that reflect new features or other changes.

### Building Python package (locally)

The build is triggered using

```shell
poetry build
```

This creates the source and wheel files in ```dist/``` subdirectory -- which
can then be uploaded or installed locally using ```pip```.

## Console output / Logging

To display console output for ordinary usage of a command line script or program
use `print()` or our own variants `print_red()` for errors, `print_yellow()` for
warnings and `print_green()` for (highlighted) positive mesages.

Events that occur during normal operation of a program (e.g. for status monitoring
or fault investigation) can use `logging.info()`. Problems in nested classes shall
be reported via `logging.warning()` or `logging.error()`

## Documentation

Please document you changes in [Changelog.md](Changelog.md). The text should help as well other contributors
as normal users to understand what has changed.

Because of the many sub-commands it is at least helpful to have in the sub-command Python file
a description which options really apply to this sub-command.

## Git Guidelines

### Workflow

We are using the [Feature Branch Workflow (also known as GitHub Flow)](https://guides.github.com/introduction/flow/),
and prefer delivery as pull requests.

Create a feature branch:

```sh
# Create and checkout the branch
git checkout -B feat/tune-vagrant-vm
```

Create Commits

```sh
# Add each modified file you'd like to include in the commit
git add <file1> <file2>

# Create a commit
git commit
```

### Git Commit

The cardinal rule for creating good commits is to ensure there is only one
"logical change" per commit. Why is this an important rule?

* The smaller the amount of code being changed, the quicker & easier it is to
  review & identify potential flaws.

* If a change is found to be flawed later, it may be necessary to revert the
  broken commit. This is much easier to do if there are not other unrelated
  code changes entangled with the original commit.

* When troubleshooting problems using Git's bisect capability, small well
  defined changes will aid in isolating exactly where the code problem was
  introduced.

* When browsing history using Git annotate/blame, small well defined changes
  also aid in isolating exactly where & why a piece of code came from.

Things to avoid when creating commits

* Mixing whitespace changes with functional code changes.
* Mixing two unrelated functional changes.
* Sending large new features in a single giant commit.

### Git Commit Conventions

We use git commit as per [Conventional Changelog](https://github.com/ajoslin/conventional-changelog):

```none
<type>(<scope>): <subject>
```

Example:

```none
feat(excel import): increase buffer size
```

Allowed types:

* **feat**: A new feature
* **fix**: A bug fix
* **docs**: Documentation only changes
* **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing
  semi-colons, newline, line endings, etc)
* **refactor**: A code change that neither fixes a bug or adds a feature
* **perf**: A code change that improves performance
* **test**: Adding missing tests
* **chore**: Changes to the build process or auxiliary tools and libraries such as
  documentation generation

You can add additional details after a new line to describe the change in detail or automatically
close a issue on Github.

```none
feat(CONTRIBUTING.md): create initial CONTRIBUTING.md

This closes #22
```

### Upstream Sync and Clean Up

Prior to submitting your pull request, you might want to do a few things to clean up your branch
and make it as simple as possible for the original repo's maintainer to test, accept, and merge
your work.

If any commits have been made to the upstream main branch, you should rebase your development
branch so that merging it will be a simple fast-forward that won't require any conflict resolution
work.

```sh
# Fetch upstream main and merge with your repo's main branch
git checkout main
git pull upstream main

# If there were any new commits, rebase your development branch
git checkout <branch-name>
git rebase main
```

Now, it may be desirable to squash some of your smaller commits down into a small number of larger
more cohesive commits. You can do this with an interactive rebase:

```sh
# Rebase all commits on your development branch
git checkout
git rebase -i main
```

This will open up a text editor where you can specify which commits to squash.

## Sign off your commits

Please sign off your commits,
to show that you agree to publish your changes under the current terms and licenses of the project.

```shell
git commit --signoff ...
```
