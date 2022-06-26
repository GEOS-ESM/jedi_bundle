#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os
import subprocess

from jedi_bundle.utils.file_system import remove_file


# --------------------------------------------------------------------------------------------------


def make_jedi(logger, config):

    # Parse the config
    modules = config['build_options']['modules']
    cmake_build_type = config['build_options']['cmake_build_type']
    path_to_build = config['build_options']['path_to_build']
    cores_to_use_for_make = config['build_options']['cores_to_use_for_make']

    bundles = config['source_code_options']['bundles']

    # Create build directory
    build_dir = os.path.join(path_to_build, f'build-{modules}-{cmake_build_type}')

    # File to hold configure steps
    for bundle in bundles:

        bundle_dir = os.path.join(build_dir, bundle)

        make_file = os.path.join(bundle_dir, 'run_make.sh')
        remove_file(logger, make_file)

        # Write steps to file
        with open(make_file, 'a') as make_file_open:
            make_file_open.write(f'#!/usr/bin/env bash \n')
            make_file_open.write(f'\n')
            make_file_open.write(f'source modules \n')
            make_file_open.write(f'\n')
            make_file_open.write(f'make -j{cores_to_use_for_make} \n')

        # Make file executable
        os.chmod(make_file, 0o755)

        # Configure command
        configure = [f'./run_make.sh']

        # Run command
        cwd = os.getcwd()
        os.chdir(bundle_dir)
        process = subprocess.run(configure)
        os.chdir(cwd)
# --------------------------------------------------------------------------------------------------
