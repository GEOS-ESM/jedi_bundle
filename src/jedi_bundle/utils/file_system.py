#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import os

# --------------------------------------------------------------------------------------------------

def remove_file(logger, pathfile):

    # Remove a file
    if (os.path.exists(pathfile)):
        try:
            os.remove(pathfile)
        except Exception as e:
            logger.abort(f'Failed to remove the existing file or directory, with excpetion: {e}.')

# --------------------------------------------------------------------------------------------------

def prompt_and_remove_file(logger, pathfile):

    if (os.path.exists(pathfile)):

        # Prompt
        logger.input(f'Need to remove {pathfile}')

        # Remove
        remove_file(logger, pathfile)

# --------------------------------------------------------------------------------------------------