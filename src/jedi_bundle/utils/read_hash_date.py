#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import re
import os

# --------------------------------------------------------------------------------------------------


def read_hash_date(pinned_config_file: str):
    # Try to read the comment in pinned_versions.yaml specifying the date
    date = 'NA'
    if os.path.isfile(pinned_config_file):
        with open(pinned_config_file) as f:
            lines = f.readlines()

        for line in lines:
            match = re.search('[0-9]{4}-[0-9]{2}-[0-9]{2}', line)
            if match:
                date = match.group()

    return date

# --------------------------------------------------------------------------------------------------
