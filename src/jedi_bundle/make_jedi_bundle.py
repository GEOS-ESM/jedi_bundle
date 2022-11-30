#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os
import subprocess

from jedi_bundle.utils.config import config_get
from jedi_bundle.utils.file_system import remove_file


# --------------------------------------------------------------------------------------------------


def make_jedi(logger, make_config):

    # Parse the config
    bundles = config_get(logger, make_config, 'bundles')
    modules = config_get(logger, make_config, 'modules')
    cmake_build_type = config_get(logger, make_config, 'cmake_build_type')
    path_to_build = config_get(logger, make_config, 'path_to_build')
    cores_to_use_for_make = config_get(logger, make_config, 'cores_to_use_for_make')

    # Modules file
    if modules != 'none':
        modules_file = os.path.join(path_to_build, 'modules')

    # File to hold configure steps
    for bundle in bundles:

        logger.info(f'')
        logger.info(f'Building the {bundle} bundle using {cores_to_use_for_make} cores')
        logger.info(f'')

        bundle_dir = os.path.join(path_to_build, bundle)

        make_file = os.path.join(bundle_dir, 'jedi_bundle_make.sh')
        remove_file(logger, make_file)

        # Write steps to file
        with open(make_file, 'a') as make_file_open:
            make_file_open.write(f'#!/usr/bin/env bash \n')
            make_file_open.write(f'\n')
            if modules != 'none':
                make_file_open.write(f'source {modules_file} \n')
            make_file_open.write(f'\n')
            make_file_open.write(f'make -j{cores_to_use_for_make} \n')

        # Make file executable
        os.chmod(make_file, 0o755)

        # Configure command
        configure = [f'./jedi_bundle_make.sh']

        # Run command
        cwd = os.getcwd()
        os.chdir(bundle_dir)
        process = subprocess.run(configure)
        os.chdir(cwd)
# --------------------------------------------------------------------------------------------------
