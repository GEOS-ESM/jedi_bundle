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
from jedi_bundle.utils.config import config_get
from jedi_bundle.utils.file_system import remove_file
from jedi_bundle.utils.yaml import load_yaml


# --------------------------------------------------------------------------------------------------


def configure_jedi(logger, configure_config):

    # Parse the config
    path_to_source = config_get(logger, configure_config, 'path_to_source')
    platform = config_get(logger, configure_config, 'platform')
    modules = config_get(logger, configure_config, 'modules')
    cmake_build_type = config_get(logger, configure_config, 'cmake_build_type', 'release')
    path_to_build = config_get(logger, configure_config, 'path_to_build')
    custom_configure_options = config_get(logger, configure_config, 'custom_configure_options', '')
    external_modules = config_get(logger, configure_config, 'external_modules', False)

    # Create build directory
    os.makedirs(path_to_build, exist_ok=True)
    os.chmod(path_to_build, 0o755)

    # Open platform dictionary
    platform_configure_directives = ''
    if platform != 'none':
        platform_pathfile = os.path.join(return_config_path(), 'platforms', platform + '.yaml')
        platform_dict = load_yaml(logger, platform_pathfile)

        if not external_modules:

            # Extra configure options for running tests
            modules_dict = platform_dict['modules'][modules]
            platform_configure_directives = config_get(logger, modules_dict, 'configure', '')

            # Create modules init file
            module_inits = config_get(logger, modules_dict, 'init', [])
            modules_init = os.path.join(path_to_build, 'modules-init')
            remove_file(logger, modules_init)
            with open(modules_init, 'a') as modules_init_open:
                for module_init in module_inits:
                    modules_init_open.write(module_init + '\n')

            # Create modules file
            module_directives = config_get(logger, modules_dict, 'load')
            modules_file = os.path.join(path_to_build, 'modules')
            remove_file(logger, modules_file)
            with open(modules_file, 'a') as modules_file_open:
                for module_directive in module_directives:
                    modules_file_open.write(module_directive + '\n')

        # Link in CRTM coefficients to source directory to avoid download
        crtm_coefficient_path_platform = platform_dict['crtm_coeffs_path']
        crtm_coefficient_version = platform_dict['crtm_coeffs_version']
        crtm_coefficient_path_source = os.path.join(path_to_source, 'test-data-release', 'crtm')
        crtm_coefficient_target = os.path.join(crtm_coefficient_path_source,
                                               crtm_coefficient_version)
        os.makedirs(crtm_coefficient_path_source, exist_ok=True)

        if not os.path.exists(crtm_coefficient_target):
            os.symlink(os.path.join(crtm_coefficient_path_platform, crtm_coefficient_version), \
                       crtm_coefficient_target)

    # File to hold configure steps
    configure_file = os.path.join(path_to_build, 'jedi_bundle_configure.sh')
    remove_file(logger, configure_file)

    # ecbuild command
    ecbuild = f'ecbuild --build={cmake_build_type} {platform_configure_directives} ' + \
              f'{custom_configure_options} -DENABLE_IODA_DATA=ON -DENABLE_UFO_DATA=ON ' + \
              f'-DENABLE_FV3_JEDI_DATA=ON {path_to_source}'
    logger.info(f'Running configure with \'{ecbuild}\'')

    # Write steps to file
    with open(configure_file, 'a') as configure_file_open:
        configure_file_open.write(f'#!/usr/bin/env bash \n')
        configure_file_open.write(f'\n')
        if not external_modules:
            configure_file_open.write(f'source {modules_init}\n')
            configure_file_open.write(f'source {modules_file}\n')
        configure_file_open.write(f'\n')
        configure_file_open.write(f'{ecbuild} \n')

    # Make file executable
    os.chmod(configure_file, 0o755)

    # Configure command
    configure = [f'./jedi_bundle_configure.sh']

    # Run command
    cwd = os.getcwd()
    os.chdir(path_to_build)
    process = subprocess.run(configure)
    logger.assert_abort(process.returncode == 0, f'Configure failed.')
    os.chdir(cwd)


# --------------------------------------------------------------------------------------------------
