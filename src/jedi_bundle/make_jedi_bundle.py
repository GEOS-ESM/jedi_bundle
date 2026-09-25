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
    cmake_build_type = config_get(logger, make_config, 'cmake_build_type')
    path_to_build = config_get(logger, make_config, 'path_to_build')
    external_modules = config_get(logger, make_config, 'external_modules', False)
    cores_to_use_for_make = config_get(logger, make_config, 'cores_to_use_for_make')

    make_file = os.path.join(path_to_build, 'jedi_bundle_make.sh')

    with open(make_file, 'w') as make_file_open:
        make_file_open.write(f'#!/usr/bin/env bash \n\n')
        if not external_modules:
            modules_init = os.path.join(path_to_build, 'modules-init')
            make_file_open.write(f'source {modules_init} \n')
            modules_load = os.path.join(path_to_build, 'modules')
            make_file_open.write(f'source {modules_load} \n\n')

            make_file_open.write(f'make -j{cores_to_use_for_make} \n')

    # Make file executable
    os.chmod(make_file, 0o755)

    # Configure command
    configure = [f'./jedi_bundle_make.sh']

    # Run command
    process = subprocess.run(configure, cwd = path_to_build)
    logger.assert_abort(process.returncode == 0, f'Make has failed.')

# --------------------------------------------------------------------------------------------------
