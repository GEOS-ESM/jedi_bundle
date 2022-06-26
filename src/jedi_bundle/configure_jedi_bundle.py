#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os
import subprocess

from jedi_bundle.config.config import return_config_path
from jedi_bundle.utils.file_system import remove_file
from jedi_bundle.utils.yaml import load_yaml


# --------------------------------------------------------------------------------------------------


def configure_jedi(logger, config):

    # Parse the config
    platform = config['build_options']['platform']
    modules = config['build_options']['modules']
    cmake_build_type = config['build_options']['cmake_build_type']
    path_to_build = config['build_options']['path_to_build']
    path_to_source = config['source_code_options']['path_to_source']

    # Create build directory
    build_dir = os.path.join(path_to_build, f'build-{modules}-{cmake_build_type}')
    os.makedirs(build_dir, exist_ok=True)
    os.chmod(build_dir, 0o755)

    # Open platform dictionary
    platform_pathfile = os.path.join(return_config_path(), 'platforms', platform + '.yaml')
    platform_dict = load_yaml(logger, platform_pathfile)

    # Steps to load the chosen modules
    module_directives = platform_dict['modules'][modules]

    # Create modules file
    modules_file = os.path.join(build_dir, 'modules')
    remove_file(logger, modules_file)
    with open(modules_file, 'a') as modules_file_open:
        for module_directive in module_directives:
            modules_file_open.write(module_directive + '\n')

    # File to hold configure steps
    configure_file = os.path.join(build_dir, 'run_configure.sh')
    remove_file(logger, configure_file)

    # ecbuild command
    ecbuild = f'ecbuild --build={cmake_build_type} -DMPIEXEC=$MPIEXEC {path_to_source}'
    logger.info(f'Running configure with \'{ecbuild}\'')

    # Write steps to file
    with open(configure_file, 'a') as configure_file_open:
        configure_file_open.write('#!/usr/bin/env bash' + '\n')
        configure_file_open.write('\n')
        configure_file_open.write('source modules' + '\n')
        configure_file_open.write('\n')
        configure_file_open.write(ecbuild + '\n')

    # Make file executable
    os.chmod(configure_file, 0o755)

    # Configure command
    configure = [f'./run_configure.sh']

    # Run command
    cwd = os.getcwd()
    os.chdir(build_dir)
    process = subprocess.run(configure)
    os.chdir(cwd)




# --------------------------------------------------------------------------------------------------
