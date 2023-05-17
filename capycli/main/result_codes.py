# -------------------------------------------------------------------------------
# Copyright 2023 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

class ResultCode(object):
    # application result codes

    # default
    RESULT_OPERATION_SUCCEEDED = 0

    # general errors as defined in https://tldp.org/LDP/abs/html/exitcodes.html
    RESULT_GENERAL_ERROR = 1

    # predefined errors from /usr/include/sysexits.h
    RESULT_COMMAND_ERROR = 64  # command was used incorrectly
    RESULT_ERROR_READING_BOM = 65  # input data was incorrect
    RESULT_FILE_NOT_FOUND = 66  # input file did not exist or was not readable
    RESULT_ERROR_ACCESSING_SERVICE = 69  # a service is unavailable
    RESULT_ERROR_WRITING_FILE = 73  # output file cannot be created
    RESULT_AUTH_ERROR = 77  # insufficient permission to perform some operation, SW360 login failed
    RESULT_ERROR_WRITING_BOM = 78

    # use 80-113 for our exit codes, see https://tldp.org/LDP/abs/html/exitcodes.html

    # custom result codes
    RESULT_NO_UNIQUE_MAPPING = 80
    RESULT_INCOMPLETE_MAPPING = 81
    RESULT_UNHANDLED_SECURITY_VULNERABILITY_FOUND = 82

    # custom errors
    RESULT_ERROR_CREATING_COMPONENT = 90
    RESULT_ERROR_CREATING_RELEASE = 91
    RESULT_ERROR_CREATING_ITEM = 92
    RESULT_NO_CACHED_RELEASES = 93
    RESULT_PROJECT_NOT_FOUND = 94
    RESULT_ERROR_ACCESSING_SW360 = 95
    RESULT_FILTER_ERROR = 96
