#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os
import subprocess

from jedi_bundle.utils.logger import colors


# --------------------------------------------------------------------------------------------------


# devnull
devnull = subprocess.DEVNULL


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
        logger.input('', f'Attempting to remove existing file: {pathfile}')

        # Remove
        remove_file(logger, pathfile)


# --------------------------------------------------------------------------------------------------


def check_for_executable(logger, executable):

    # Check for executable
    rc = subprocess_run(logger, ['which', executable], False)
    if rc != 0:
        logger.abort(f'Did not find {executable} in the path')


# --------------------------------------------------------------------------------------------------


def subprocess_run(logger, command, abort_on_fail=True):

    # Prepare command
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Run process
    output, error = p.communicate()

    # Abort message if monitoring failure
    if p.returncode != 0 and abort_on_fail:
        join_command = ' '.join(command)
        error_str = error.decode("utf-8")
        logger.abort(f'In subprocess_run the command \'{join_command}\' failed with ' +
                     f'error {error_str}.')

    # Return error code
    return p.returncode


# --------------------------------------------------------------------------------------------------
