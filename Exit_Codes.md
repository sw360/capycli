<!--
# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
-->

# CaPyCli - Clearing Automation Python Command Line Tool

Starting with version 1.9.1, CaPyCLI systematically uses application exit codes
to inform about errors or application results. We tried use best practices from
/usr/include/sysexits.h and https://tldp.org/LDP/abs/html/exitcodes.html.

| Exit Code     | Description                                    |
|:--------------|:-----------------------------------------------|
| 0             | Default exit code, operation succeeded         |

## Error Codes

| Exit Code     | Description                                    |
|:--------------|:-----------------------------------------------|
| 1             | General error                                  |
| 64            | Unknown command or sub-command                 |
| 65            | Error reading SBOM file                        |
| 66            | Input file not found                           |
| 69            | Error accessing external service, e.g. Github  |
| 73            | Error writing file                             |
| 77            | Error during login, e.g. to SW360              |
| 90            | Error creating SW360 component                 |
| 91            | Error creating SW360 release                   |
| 92            | Error creating SW360 item                      |
| 93            | No cached release available                    |
| 94            | SW360 project not found                        |
| 95            | Error accessing SW360                          |
| 96            | Error during filter operation                  |

## Result Codes (80-89)

| Exit Code     | Description                                      |
|:--------------|:-------------------------------------------------|
| 80            | No unique mapping has been found ('bom map')     |
| 81            | Incomplete mapping ('bom map', mode switch used) |
| 82            | Unhandled security vulnerabilities found         |
